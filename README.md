# Vulnleap Webapp

The Vulnleap webapp is the actual vulnerable web application, built on Flask/Python. It is full of intentional vulnerabilities for training purposes. The app is a mortgage app, with four types of users:

- Unauthenticated users, only able to get a quote but not save unless they create an account
- Normal users, who can have saved quotes, or a mortgage in progress, or a mortgage they are paying off.
- Admin users, who are intended to be Vulnleap employees only, able to see all mortgage accounts as well as details of users. They can also reset MFA for users who call in for support and are locked out.
- Superadmin users, who are a select group of high ranking people at Vulnleap who have access to do dangerous functions like changing mortgage amounts, deleting mortgages, and controlling overall settings for where mortgage payments are routed to.


## Tech Stack
- Containerized
- Flask/python web app
- MariaDB database