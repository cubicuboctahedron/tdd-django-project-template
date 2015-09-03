# Test-Driven Django project all-in-one setup

Used to setup everything I need to work with Django-based projects.

This will setup development Vagrant-managed VM with django and TDD suite. Also contains routines and configs to deploy to production with the following setup:
- Supervisor
- Nginx
- Uwsgi/Django
- Postgres
- Uwsgi/Websockets (if enabled, using the ws4redis package)
- Celery (if enabled) with Flower (in a Docker container)

Workflow:
- fork this repo
- update Vagrantfile with your settings:
 - `PROJECT_NAME` - your django project name
 - `PROJECT_HOST_NAME` - your project URL
 - `IP` - virtual machine IP address
- call `vagrant up`
This will deploy a VM with the django project, packages and my base test suite. You can ssh to it using the `vagrant ssh` command.
- `git commit -a && git push` to update project name and settings that were set while the vagrant deployment
- Update settings in the `deploy/fabfile.py` fabric script, add your repository SSH keys to the `deploy/keys` and your HTTPS certificates to `deploy/certs`
- deploy to production site with `fab deploy:host=your.host.name` command executed from the `/sites/PROJECT_NAME/deploy` folder on VM

**Please note that this is a work in progress project.**
