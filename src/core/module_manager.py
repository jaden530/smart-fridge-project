# src/core/module_manager.py

class ModuleManager:
    def __init__(self):
        self.modules = {}

    def register_module(self, name, module):
        self.modules[name] = module

    def get_module(self, name):
        return self.modules.get(name)

    def list_modules(self):
        return list(self.modules.keys())