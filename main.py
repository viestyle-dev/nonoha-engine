import nonoha_engine
from nonoha_engine.runtime_config import RuntimeConfig

if __name__ == "__main__":
    nonoha_engine.run(RuntimeConfig(includes_fbc_commands=True))
