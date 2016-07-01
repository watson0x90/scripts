function Get-FolderACL 
{
    [CmdletBinding()]
	
    param(
        [Parameter(Mandatory = $true, position = 0)]
        [ValidateNotNullOrEmpty()]
        [String] $Path
		
    )

    $PathsToSearch = (Get-ChildItem $Path |
        Where-Object -FilterScript {
            $_.PSIsContainer 
        } |
    Select-Object -ExpandProperty FullName)

    $weakacls = New-Object -TypeName PSObject
    
    foreach($folder in $PathsToSearch)
    {
        $AccessList = ((Get-Item $folder).GetAccessControl('Access')).Access
        foreach($permission in $AccessList)
        {
            if($permission.IdentityReference -like '*domain users*' -or $permission.IdentityReference -like '*everyone*')
            {
                Add-Member -InputObject $weakacls -MemberType NoteProperty -Name Path -Value $folder
                Add-Member -InputObject $weakacls -MemberType NoteProperty -Name GroupAccess -Value $permission.IdentityReference
                Add-Member -InputObject $weakacls -MemberType NoteProperty -Name FileSystemRights -Value $permission.FileSystemRights
            }
        }
    }

    $weakacls | Format-List
}
