from balder.types.mutation.base import BalderMutation
import graphene
import logging
import namegenerator
from lok import bounced
from arkitekt.comfort import reset_repository

class ResetReturn(graphene.ObjectType):
    ok = graphene.Boolean()


class Reset(BalderMutation):
    """Create Repostiory"""

    class Arguments:
        pass

    class Meta:
        type = ResetReturn 

    
    @bounced(anonymous=True) 
    def mutate(root, info, exclude=[],  name=None):

        reset_repository()
        
        return {"ok": True}