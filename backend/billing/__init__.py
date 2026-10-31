"""Proxy module allowing `import billing` or `from billing.models import ...`
to resolve directly to `apps.billing`.
"""
import sys
from apps import billing as _billing_app
from apps.billing import generation as _generation
from apps.billing import pipeline as _pipeline
from apps.billing import models as _models
from apps.billing import services as _services
from apps.billing.services import calculation as _calculation
from apps.billing.services import allocation as _allocation
from apps.billing.services import recurring as _recurring
from apps.billing.services import adapters as _adapters
from apps.billing.services import numbering as _numbering
from apps.billing.services import pdf as _pdf
from apps.billing.services import storage as _storage
from apps.billing.services import emailing as _emailing

sys.modules["billing"] = _billing_app
sys.modules["billing.models"] = _models
sys.modules["billing.generation"] = _generation
sys.modules["billing.pipeline"] = _pipeline
sys.modules["billing.services"] = _services
sys.modules["billing.services.calculation"] = _calculation
sys.modules["billing.services.allocation"] = _allocation
sys.modules["billing.services.recurring"] = _recurring
sys.modules["billing.services.adapters"] = _adapters
sys.modules["billing.services.numbering"] = _numbering
sys.modules["billing.services.pdf"] = _pdf
sys.modules["billing.services.storage"] = _storage
sys.modules["billing.services.emailing"] = _emailing
