"""Proxy module allowing `import billing` or `from billing.models import ...`
to resolve directly to `apps.billing`.
"""
import sys
from apps import billing as _billing_app

# Re-export all submodules
sys.modules["billing"] = _billing_app
sys.modules["billing.models"] = _billing_app.models
sys.modules["billing.generation"] = _billing_app.generation
sys.modules["billing.pipeline"] = _billing_app.pipeline
sys.modules["billing.services"] = _billing_app.services
sys.modules["billing.services.calculation"] = _billing_app.services.calculation
sys.modules["billing.services.allocation"] = _billing_app.services.allocation
sys.modules["billing.services.recurring"] = _billing_app.services.recurring
sys.modules["billing.services.adapters"] = _billing_app.services.adapters
sys.modules["billing.services.numbering"] = _billing_app.services.numbering
sys.modules["billing.services.pdf"] = _billing_app.services.pdf
sys.modules["billing.services.storage"] = _billing_app.services.storage
sys.modules["billing.services.emailing"] = _billing_app.services.emailing

