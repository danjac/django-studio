**/dj-create-model <app_name> <model_name>**

Designs and writes a Django model with factory, fixture, and tests.

Interactive: asks for field definitions (name, type, options), timestamps, and
whether to register in the admin. Prints a model sketch and waits for
confirmation before writing any code. Offers to generate CRUD views once
tests pass.

Example:
  /dj-create-model store Product
