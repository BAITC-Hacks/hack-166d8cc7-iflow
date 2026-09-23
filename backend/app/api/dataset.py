from fastapi import APIRouter, Request, Depends, UploadFile, File
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from pydantic import ValidationError
from app.core.auth import resolve_principal, require_hr
from app.core.errors import DomainError, STATUS
from app.api.dependencies import hr_context, RequestContext
from app.repositories.dataset import parse_employees
from app.repositories.history import parse_history
from app.repositories.validation import SourceValidationError
from app.schemas.responses import ImportResult
from app.services.dataset import import_dataset

LIMIT=10*1024*1024
router=APIRouter(prefix="/api/dataset",tags=["dataset"])

class ImportGuard:
    """Bound the complete multipart body before the framework parses it."""
    def __init__(self,app,identities):
        self.app,self.identities=app,identities
    async def __call__(self,scope,receive,send):
        if scope["type"]!="http" or scope["path"]!="/api/dataset/import" or scope["method"]!="POST":
            return await self.app(scope,receive,send)
        try:
            headers=dict(scope["headers"])
            p=resolve_principal(headers.get(b"authorization",b"").decode(),self.identities)
            require_hr(p)
            data=bytearray()
            while True:
                message=await receive()
                if message["type"]=="http.disconnect": return
                data.extend(message.get("body",b""))
                if len(data)>LIMIT: raise DomainError("too_large","Import exceeds 10 MiB")
                if not message.get("more_body",False): break
        except DomainError as err:
            response=JSONResponse(status_code=STATUS[err.code],content={"error":{"code":err.code,"message":err.message,"details":[]}},headers={"Cache-Control":"no-store"})
            return await response(scope,receive,send)
        delivered=False
        async def replay():
            nonlocal delivered
            if not delivered:
                delivered=True
                return {"type":"http.request","body":bytes(data),"more_body":False}
            return await receive()
        await self.app(scope,replay,send)

@router.post("/import",response_model=ImportResult)
async def upload(request: Request,employees: UploadFile | None=File(default=None),
                 history: UploadFile | None=File(default=None),ctx: RequestContext=Depends(hr_context)):
    try:
        emp=await employees.read(LIMIT+1) if employees else None
        hist=await history.read(LIMIT+1) if history else None
        if sum(len(b) for b in (emp,hist) if b is not None)>LIMIT: raise DomainError("too_large","Import exceeds 10 MiB")
        parsed_employees=parse_employees(emp) if emp is not None else None
        parsed_history=parse_history(hist) if hist is not None else None
    except (ValueError,UnicodeError) as err:
        details=err.details if isinstance(err,SourceValidationError) else [{"loc":["employees.json",*e["loc"]],"type":e["type"],"message":"Invalid value"} for e in err.errors()] if isinstance(err,ValidationError) else []
        raise DomainError("invalid","Uploaded files do not match the dataset schema",details) from err
    finally:
        if employees: await employees.close()
        if history: await history.close()
    return await run_in_threadpool(import_dataset,ctx.principal,parsed_employees,parsed_history,request.app.state.dataset)
