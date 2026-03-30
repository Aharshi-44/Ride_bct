"""
Compatibility tweaks for XAMPP MariaDB 10.4:

- Django 6 expects MariaDB 10.6+ (minimum_database_version).
- Django enables INSERT ... RETURNING for all MariaDB; that syntax exists only in MariaDB 10.5+,
  so 10.4 must report can_return_columns_from_insert = False.
"""

from django.db.backends.mysql.features import DatabaseFeatures as MySQLDatabaseFeatures
from django.utils.functional import cached_property


class DatabaseFeatures(MySQLDatabaseFeatures):
    @cached_property
    def minimum_database_version(self):
        if self.connection.mysql_is_mariadb:
            return (10, 4)
        return (8, 0, 11)

    @cached_property
    def can_return_columns_from_insert(self):
        if self.connection.mysql_is_mariadb:
            return self.connection.mysql_version >= (10, 5)
        return False
