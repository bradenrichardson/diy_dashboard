- v2.0 - A user doesn't have an AWS account, but banks with UP
    - User interface
        - Register Data Source - Up
            - Create Webhook
            - Download Historical
        - Provision Environment
    - Provisioned AWS resources as a service

- v3.0 - A user doesn't have an AWS account, and doesn't bank with up
    - Register multiple data sources
    - Multiple dashboard integrations


### API
Potential Methods
```
ProvisionDashboardEnv(**kwargs)
    { 
        up_api_key,
        aws_access_key,
        secret_access_key,
        tableau_user_name,
        tableau_password,
        tableau_site_name
    }

DeleteDashboardEnv(environment)

UpdateDashboardEnv(**kwargs)
    {
        environment,
        up_api_key,
        aws_access_key,
        secret_access_key,
        tableau_user_name,
        tableau_password,
        tableau_site_name
    }

GetDashboardEnv(environment)

ListDashboardEnvs()
```

### User interaction options
0. Parameters -> cloudformation
1. Config file -> pipeline
2. Web ui -> api
3. Request -> api
4. Deploy infrastructure stack

