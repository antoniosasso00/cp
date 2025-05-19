# Esporta gli schemi principali per un più facile import
# Ad esempio:
# from .user import UserCreate, UserUpdate, UserResponse

# Questi verranno implementati durante lo sviluppo delle funzionalità 

from .catalogo import CatalogoBase, CatalogoCreate, CatalogoUpdate, CatalogoResponse
from .parte import ParteBase, ParteCreate, ParteUpdate, ParteResponse
from .tool import ToolBase, ToolCreate, ToolUpdate, ToolResponse
from .autoclave import AutoclaveBase, AutoclaveCreate, AutoclaveUpdate, AutoclaveResponse, StatoAutoclaveEnum
from .ciclo_cura import CicloCuraBase, CicloCuraCreate, CicloCuraUpdate, CicloCuraResponse 