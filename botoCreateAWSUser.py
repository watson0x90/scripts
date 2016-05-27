#!/usr/bin/python
import boto
'''
Use this script at your own risk. I am not repsonsible for any disruption or impact this may cause. 
Remeber you found this on the interwebs!
'''

# Enter in Access & Secret Key
ACCESS_KEY = ""
SECRET_KEY = ""
account_perm_policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"

# Enter in Username and Password for new account
new_account_name = ""
new_account_password = ""

def create_account():
    #connect to IAM
    iam = boto.connect_iam(ACCESS_KEY,SECRET_KEY)

    #create user
    iam.create_user(new_account_name)

    #add user to group
    iam.add_user_to_group("Administrators", new_account_name)

    #create access keys
    keys = iam.create_access_key(new_account_name)
    
    # try statements to attach user to policy.
    # some versions of boto do not have attach_user_policy, however put_user_policy
    try:
        iam.attach_user_policy(account_perm_policy_arn,new_account_name)
    except:
        print "[-] Unable to execute method 'attach_user_policy()'"
        print "[-] Attempting put_user_policy "
        try:
            iam.put_user_policy(new_account_name,account_perm_policy_arn)
        except:
            print "[-] Failed executing method 'put_user_policy()'"
            print "[-] Execute command: aws iam attach-user-policy --policy-arn arn:aws:iam::aws:policy/AdministratorAccess --user-name %s" % new_account_name
        
    #create AWS Web Console Login
    iam.create_login_profile(new_account_name,new_account_password)

    print "User %s created with password %s" % (new_account_name, new_account_password)
    print "Access Key ID: %s" % str(keys.access_key_id)
    print "Secret Key ID %s" % str(keys.secret_access_key)

create_account()
