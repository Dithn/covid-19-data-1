from cowidev.testing.incremental import __all__ as incremental
from cowidev.testing.batch import __all__ as batch


# Import modules
country_to_module_batch = {c: f"cowidev.testing.batch.{c}" for c in batch}
country_to_module_incremental = {c: f"cowidev.testing.incremental.{c}" for c in incremental}
country_to_module = {
    **country_to_module_batch,
    **country_to_module_incremental,
}
MODULES_NAME_BATCH = list(country_to_module_batch.values())
MODULES_NAME_INCREMENTAL = list(country_to_module_incremental.values())
MODULES_NAME = MODULES_NAME_BATCH + MODULES_NAME_INCREMENTAL
