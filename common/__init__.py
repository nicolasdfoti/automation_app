"""Common layer for the Automation Suite.

Neutral, app-agnostic code shared by the future Target System and Automation
System applications. This package is deliberately free of any application
dependency: it must never import ``backend``, ``target_system``,
``automation_system``, routers or any frontend code. Only the standard
library and the shared Excel/data store are allowed.
"""