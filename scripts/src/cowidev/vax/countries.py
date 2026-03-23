from cowidev.vax.incremental import __all__ as incremental
from cowidev.vax.batch import __all__ as batch


# Import modules
country_to_module_batch = {c: f"cowidev.vax.batch.{c}" for c in batch}
country_to_module_incremental = {c: f"cowidev.vax.incremental.{c}" for c in incremental}
country_to_module = {
    **country_to_module_batch,
    **country_to_module_incremental,
}
MODULES_NAME_BATCH = list(country_to_module_batch.values())
MODULES_NAME_INCREMENTAL = list(country_to_module_incremental.values())
MODULES_NAME = MODULES_NAME_BATCH + MODULES_NAME_INCREMENTAL
