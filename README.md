[![Build Status](https://travis-ci.org/passiopeia/passiopeia-hub.svg?branch=master)](https://travis-ci.org/passiopeia/passiopeia-hub)
[![Coverage Status](https://coveralls.io/repos/github/passiopeia/passiopeia-hub/badge.svg?branch=master)](https://coveralls.io/github/passiopeia/passiopeia-hub?branch=master)

# Passiopeia Hub

The Passiopeia Hub is a Django based Web Application that provides the backend for synchronization.

---

# Getting started

Passiopeia Hub is currently under heavy development end far away from being production ready. This is a short guide to
set up your development environment and get you started.

## Requirements

You need Python 3.6, 3.7 or 3.8. We recommend Python 3.8 for development, but keep in mind that we still support Python
3.6. The Travis CI build plan is configured to use Python in all supported versions. Install Python through the package
manager of your OS or grab your copy at [https://www.python.org/downloads/](https://www.python.org/downloads/).

As the only browser for testing at the moment (more to come), we support Mozilla's Firefox. If you don't have Firefox,
get it here: [https://www.mozilla.org/de/firefox/all/](https://www.mozilla.org/de/firefox/all/).

Additionally, you need Node.js in the latest LTS version for the yarn package manager (for the managed static files) and
the geckodriver (for using selenium with Firefox):

1. Download and install Node.js: [https://nodejs.org/en/download/](https://nodejs.org/en/download/)
2. Install yarn: `npm install -g yarn`
3. Install geckodriver: `npm install -g geckodriver`

On your mobile phone, you need a TOTP app that is able to be configured with a QR code. You can test your app with the
example under "[Example for an OTP secret](#example-for-an-otp-secret)", as not all apps allow secrets longer than 11
bytes.

## Checkout and setup

1. Clone the Passiopeia Hub repository, e.g. into the folder `/home/developer/passiopeia-hub`
2. `cd /home/developer/passiopeia-hub`
3. Create a new Python virtual environment, e.g. with Python 3.8: `python3.8 -m venv venv`
4. Activate the Python virtual environment: `. venv/bin/activate`
5. Install the requirements: `pip install -r requirements.txt`
6. Install the test requirements: `pip install -r test-requirements.txt`
7. Install the managed static files: `(cd hub_app/static/hub_app/managed && yarn install)` (mind the brackets)
8. Compile the static files: `./manage.py collectstatic`
9. Compile the messages (for German translation): `./manage.py compilemessages -l de`
10. Create the test database: `./manage.py migrate`
11. Create a Superuser: `./manage.py createsuperuser` and enter the required data. If you don't know what to enter for
the OTP secret, see [Example for an OTP secret](#example-for-an-otp-secret).
12. Run the tests (optional): `./manage.py test --settings=hub.test_settings`
13. Start the development server: `./manage.py runserver --settings=hub.test_settings`
14. Open your browser at: [http://localhost:8000/](http://localhost:8000/)

## Example for an OTP secret

Scan this QR Code:

![Development Secret](doc_files/development-secret.png)

Use this as a secret during super user generation:

`TLSN6XBSSBF5SGXMIH3UO2OYJHVB64CA6YHHKSMPW7AIEEHGAXAQCNPMQ4UBZ74FLOJRBDGOLAHZY3Q76DICPRXNIQPZ6JD5HZ5R2OTIKWDE5AQWB6TQ====`

**A word of warning:** Please make sure that you immediately change your OTP secret after your first login as a super
user. Use the "My Account" > "Hub Credentials" > "OTP Secret" page for that purpose. If you are still on your local
machine, you can use this link:
[http://localhost:8000/hub/my-account/credentials/otp-secret](http://localhost:8000/hub/my-account/credentials/otp-secret). 

### Still have OTP problems?

- In most cases, the date/time between your smartphone and the machine where Passiopeia Hub runs is out of sync. While
smartphones are mostly time-synced by the network, the machine running Passiopeia Hub should use a NTP time source.
- Maybe your App is not as compatible as expected. If you have Passiopeia Hub up and running on your machine, browse to
[http://localhost:8000/hub/support/test-your-app](http://localhost:8000/hub/support/test-your-app). This page contains
a QR code to scan and a test for a valid one-time password.

## E-Mail Handling

The application sends e-mails, e.g. when registering a new user or using the "Forgotten Credentials" workflow. Django is
configured to save all these e-mails to the folder `_e-mail/` instead of trying to deliver them. This is configured in
the `hub/settings.py` file. If you want the application to send the e-mails to real recipients, you need to change the
configuration accordingly.

Good to know: If an e-mail is send during a `TestCase`, e-mails are neither delivered nor saved to a file. Tests can
access the mails though `mail.outbox`. See the `hub_app/tests/test_registration.py` for an example.

## JSON Schema

The Passiopeia Hub comes with a complete set of JSON Schemas for all requests to the services and responses from the
services. All Schemas are listed at the endpoint `/schema/` (on your local machine: 
[http://localhost:8000/schema/](http://localhost:8000/schema/)). Sorry for the stylesheet.
 
We make heavy use of `$ref`, and to make sure that URL resolvers of JSON Schema Validators work, you can set the JSON
Schema Prefix in your `settings.py`.

---

# Pull Requests

We are happy to receive your pull request. But we require you to keep up the code coverage with tests. Code coverage is
automatically calculated during the Travis CI builds and reported by Coveralls in every pull request.
