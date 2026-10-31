![Banner](banner.png)

# chv-ServiceAccountPrivilegeChecker
Validates a service account configuration file (YAML or JSON) against a JSON schema you supply, and reports every place the config breaks that schema, with the failing path and the schema message. The tool ships with no built in list of allowed or forbidden privileges: privilege limits exist only if the schema you supply encodes them, for example by listing the allowed permission values in an enum. With a schema that only checks that fields are present, a config granting admin, root, and sudo passes as valid. The check is static and file based, with no runtime monitoring.

## Install
`git clone https://github.com/ShadowStrikeHQ/chv-serviceaccountprivilegechecker`

## Usage
`./chv-serviceaccountprivilegechecker [params]`

## Parameters
- `-h`: Show help message and exit
- `-l`: Set the logging level.
- `-o`: No description provided

## License
Copyright (c) ShadowStrikeHQ
