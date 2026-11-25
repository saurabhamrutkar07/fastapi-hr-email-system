<#
Turn the EC2 server on and off from the laptop.

Usage (from the repo folder, in PowerShell):
    .\scripts\server.ps1 status   # is it on? which IP? is the site up?
    .\scripts\server.ps1 start    # start, open SSH for this laptop, wait for the site
    .\scripts\server.ps1 stop     # back up the database to S3, then stop
    .\scripts\server.ps1 ssh      # open SSH for this laptop and log in

What it needs:
    - AWS CLI with the "coldreach" profile (aws configure --profile coldreach).
      That IAM user (coldreach-laptop) can only start/stop this one server
      and change the SSH rule on its firewall: deploy/iam-laptop-policy.json
    - The SSH key file at $KeyPath below
    - Optional: UPTIMEROBOT_API_KEY as a Windows user environment variable. 
      start resumes the uptime monitor, stop pauses it, so a planned stop 
      does not send "site down" emails.

The domain's DNS is not changed from here: the server updates Cloudflare
itself on every boot (deploy/cloudflare-ddns.sh).
#>

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("status", "start", "stop", "ssh")]
    [string]$Action,

    # Stop even if the backup fails (only when you know why it failed)
    [switch]$SkipBackup
)

# Stop the script on the first PowerShell error
$ErrorActionPreference = "Stop"

# ------------------------------------------------------------
# Settings (none of these are secrets)
# ------------------------------------------------------------
$AwsProfile = "coldreach"
$Region     = "ap-south-1"
$InstanceId = "i-00cb1f1ffe7b4eeec"
$SgId       = "sg-0b992f200d483e102"     # coldreach-sg
$Domain     = "saurabhamrutkar.com"
$KeyPath    = "$HOME\Documents\sshkey\coldreach-key.pem"
$BackupCmd  = "/home/ubuntu/coldreach-backup.sh"
$UptimeMonitorId = "804808359"

# A new terminal finds "aws" on PATH; an old one may not, so fall back
$Aws = (Get-Command aws -ErrorAction SilentlyContinue).Source
if (-not $Aws) { $Aws = "C:\Program Files\Amazon\AWSCLIV2\aws.exe" }


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

# Run an AWS CLI command with our profile and region; return parsed JSON
function Invoke-Aws {
    $out = & $Aws @args --profile $AwsProfile --region $Region --output json
    if ($LASTEXITCODE -ne 0) { throw "AWS command failed: aws $($args -join ' ')" }
    if ($out) { return ($out -join "`n" | ConvertFrom-Json) }
}

# Current state ("running", "stopped", ...) and public IP of the server
function Get-Server {
    return Invoke-Aws ec2 describe-instances --instance-ids $InstanceId `
        --query "Reservations[0].Instances[0].{State:State.Name,Ip:PublicIpAddress}"
}

# Let SSH (port 22) in from this laptop's current internet IP only.
# Home internet IPs change, so the old laptop IP rule is removed.
function Update-SshRule {
    $myCidr = (Invoke-RestMethod -Uri "https://checkip.amazonaws.com").Trim() + "/32"

    $rules = (Invoke-Aws ec2 describe-security-group-rules `
        --filters "Name=group-id,Values=$SgId").SecurityGroupRules
    $sshRules = @($rules | Where-Object { -not $_.IsEgress -and $_.FromPort -eq 22 })

    if ($sshRules | Where-Object { $_.CidrIpv4 -eq $myCidr }) {
        Write-Host "SSH already allowed from $myCidr"
        return
    }

    # Add the new rule first, then remove the old ones
    Invoke-Aws ec2 authorize-security-group-ingress --group-id $SgId `
        --protocol tcp --port 22 --cidr $myCidr | Out-Null
    foreach ($rule in $sshRules) {
        Invoke-Aws ec2 revoke-security-group-ingress --group-id $SgId `
            --security-group-rule-ids $rule.SecurityGroupRuleId | Out-Null
    }
    Write-Host "SSH now allowed from $myCidr (old laptop IP removed)"
}

# Run a command on the server over SSH.
# HostKeyAlias: the server's key is remembered under one name, not per IP,
# so a new IP after every start does not ask "are you sure?" again,
# but a different key (a different machine) is still refused.
function Invoke-Ssh([string]$Ip, [string]$Command) {
    $sshArgs = @("-i", $KeyPath, "-o", "HostKeyAlias=coldreach-server",
                 "-o", "StrictHostKeyChecking=accept-new", "ubuntu@$Ip")
    # No command = interactive login
    if ($Command) { $sshArgs += $Command }
    & ssh @sshArgs
}

# HTTP status of /api/health, asked straight from the server's IP
# (so it works even before the laptop's DNS cache has the new IP)
function Get-Health([string]$Ip) {
    return (& curl.exe -s -o NUL -w "%{http_code}" --max-time 5 `
        --resolve "${Domain}:443:$Ip" "https://$Domain/api/health")
}

# Pause (0) or resume (1) the UptimeRobot monitor, so a planned stop 
# does not send "site down" emails. The API key is a Windows user
# environment variable, never in a repo. 
# If this fails, only warn: starting/stopping the server matters more.
function Set-UptimeMonitor([int]$Status) {
    $key = [Environment]::GetEnvironmentVariable("UPTIMEROBOT_API_KEY","User")
    if (-not $key) {
        Write-Warning "UPTIMEROBOT_API_KEY is not set, uptime monitor not chenged"
        return
    }
    try { 
        $r = Invoke-RestMethod -Method Post -Uri "https://api.uptimerobot.com/v2/editMonitor" `
        -Body @{ api_key = $key; id = $UptimeMonitorId; status = $Status; format = "json" }
        if ($r.stat -ne "ok") { throw ($r.error | ConvertTo-Json -Compress) }
        $word = if ($Status -eq 1 ) { "resumed" } else { "paused" } 
        Write-Host "Uptime monitor $word" 
    } catch {
        Write-Warning "Could not change the uptime monitor: $_"
    }
}


# ------------------------------------------------------------
# Actions
# ------------------------------------------------------------

function Show-Status {
    $server = Get-Server
    Write-Host "Server : $($server.State)"
    if ($server.State -ne "running") { return }

    Write-Host "IP     : $($server.Ip)"
    $dns = (Resolve-DnsName $Domain -Server 1.1.1.1 -Type A -DnsOnly |
        Where-Object { $_.Type -eq "A" } | Select-Object -First 1).IPAddress
    $match = if ($dns -eq $server.Ip) { "OK" } else { "not updated yet" }
    Write-Host "DNS    : $Domain -> $dns ($match)"
    Write-Host "Health : $(Get-Health $server.Ip)"
}

function Start-Server {
    $server = Get-Server
    if ($server.State -eq "stopped") {
        Write-Host "Starting server..."
        Invoke-Aws ec2 start-instances --instance-ids $InstanceId | Out-Null
    } elseif ($server.State -ne "running") {
        Write-Host "Server is '$($server.State)', waiting for it to be running..."
    }
    Invoke-Aws ec2 wait instance-running --instance-ids $InstanceId
    $server = Get-Server
    Write-Host "Running at $($server.Ip)"

    Update-SshRule

    # The laptop may still remember the old IP for the domain
    ipconfig /flushdns | Out-Null

    # On boot the server pulls the latest code and rebuilds if needed
    # (deploy/coldreach-deploy.service), so give it up to 5 minutes
    Write-Host "Waiting for the site..."
    for ($i = 0; $i -lt 60; $i++) {
        if ((Get-Health $server.Ip) -eq "200") {
            Write-Host "Site is up: https://$Domain"
            Set-UptimeMonitor 1
            Show-Status
            return
        }
        Start-Sleep -Seconds 5
    }
    # Resume anyway: if the site stays down, the monitor should alert 
    Set-UptimeMonitor 1 
    Write-Warning "Site did not answer in 5 minutes. Log in with: .\scripts\server.ps1 ssh"
}

function Stop-Server {
    $server = Get-Server
    if ($server.State -ne "running") {
        Write-Host "Server is already '$($server.State)'"
        return
    }

    if (-not $SkipBackup) {
        Update-SshRule
        Write-Host "Backing up the database to S3..."
        Invoke-Ssh $server.Ip $BackupCmd
        if ($LASTEXITCODE -ne 0) {
            throw "Backup failed, so the server was NOT stopped. Check it, or use -SkipBackup."
        }
    }

    # Planned stop: pause the monitor first, so it does not email "site down"
    Set-UptimeMonitor 0

    Write-Host "Stopping server..."
    Invoke-Aws ec2 stop-instances --instance-ids $InstanceId | Out-Null
    Invoke-Aws ec2 wait instance-stopped --instance-ids $InstanceId
    Write-Host "Server stopped. No compute charge until the next start."
}

function Enter-Server {
    $server = Get-Server
    if ($server.State -ne "running") { throw "Server is '$($server.State)'. Run: .\scripts\server.ps1 start" }
    Update-SshRule
    Invoke-Ssh $server.Ip ""
}


switch ($Action) {
    "status" { Show-Status }
    "start"  { Start-Server }
    "stop"   { Stop-Server }
    "ssh"    { Enter-Server }
}
