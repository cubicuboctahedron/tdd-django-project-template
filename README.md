# Test-Driven Django project cookiecutter template

Used to create new django project with settings and packages I use.

Also includes:
- base test suite classes and routines I use in TDD workflow
- deployment scripts (Fabric-based)
- Vagrant-managed development VM

Workflow
--------
- install [cookiecutter](https://github.com/audreyr/cookiecutter)

- run `cookiecutter git@github.com:cubicuboctahedron/tdd-django-project-template.git`
 You will need to answer these questions in order to generate your project:
 - `vm_dotfile_configs_repo_url (default is "")?` - use your custom . configs in [Mathias’s dotfiles](https://github.com/mathiasbynens/dotfiles) format
 - `vm_ip (default is "10.10.10.100")?` - IP address of the dev VM
 - `project_name (default is "project_name")?` - name of the project
 - `repo_name (default is "project_name")?` - repo and django project name, without spaces
 - `author_name (default is "Your Name")?` - your name
 - `email (default is "Your email")?` - your email
 - `description (default is "A short description of the project.")?` - project description (will be added to the readme file)
 - `domain_name (default is "example.com")?` - production server URL
 - `use_celery (default is "n")?` - use or not celery (all emails will be sent by celery delayed tasks)
 - `use_websockets (default is "n")?` - adds websocket support with the [ws4redis](https://github.com/jrief/django-websocket-redis) package
 - `use_rest_framework (default is "n")?`  - adds [Django REST framework](https://github.com/tomchristie/django-rest-framework)
    
 You can now initialize GIT repository and push your project:

 ```
 git init
 git add .
 git commit -m "initial commit"
 git remote add origin git@github.com:cubicuboctahedron/yet_another_project.git
 git push -u origin master
 ```

- run `vagrant up`
 This will deploy a VM with the django project, packages and my base test suite. 
 You can ssh to it using the `vagrant ssh` command.

- Update settings in the `deploy/fabfile.py` fabric script, add your repository SSH keys to the `deploy/keys` and your HTTPS certificates to `deploy/certs`

- deploy to production site with `fab deploy:host=your.host.name` command executed from the `deploy` folder on VM

Production environment
----------------------
My production environment setup is based on:
- Supervisor
- Nginx
- Uwsgi/Django
- Postgres
- Uwsgi/Websockets (if enabled, using the ws4redis package)
- Celery (if enabled) with Flower (in a Docker container)

Config templates can be found in `deploy/configs`.

Notes
-----
**Please note that this is a work in progress project.**

Thanks
-----
- to [pydanny](https://github.com/pydanny) for the  [cookiecutter-django](https://github.com/pydanny/cookiecutter-django) project

- to [hjwp](https://github.com/hjwp) for the book [Test-Driven Development with Python](http://chimera.labs.oreilly.com/books/1234000000754)
