* Store the plugin in the Redmine plugin directory. The sample docker-compose.yml plugin directory is `./redmine/plugins`

* Enter the Redmine container and execute the following command
```
bundle install --without development test --no-deployment
bundle exec rake redmine:plugins NAME=redmine_agile RAILS_ENV=production
```
