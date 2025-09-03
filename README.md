# backend-actions

## Database migration

Check if the database update files will result in the same output as the schema file.
> [!CAUTION]
> This action is work in progress.

## Decomposer

Check if decomposer defines a singular stack of libraries.
Will fail if you're mixing library versions and the stack depends on more than one version.

> [!CAUTION]
> This action is work in progress.

## Reviewboard

Check if the commit has a review attached to it and if so,
if the review has ship-its.

## PHPUnit Config

Check if the `tests/phpunit.xml` file matches the standards for a Framna Amsterdam PHPUnit config.
