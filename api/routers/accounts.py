from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from queries.accounts import AccountQueries, AccountIn, AccountOut, AccountListOut, DuplicateAccountError
from typing import Optional
from psycopg.errors import ForeignKeyViolation
from jwtdown_fastapi.authentication import Token
from authenticator import authenticator
from pydantic import BaseModel


class AccountForm(BaseModel):
    username: str
    password: str

class AccountToken(Token):
    account: AccountOut

class HttpError(BaseModel):
    detail: str

router = APIRouter()





@router.get("/api/accounts/{username}", response_model = Optional[AccountOut])
def get_account(
    username: str,
    queries: AccountQueries = Depends(),
    ):
    record = queries.get_account(username)
    if record is None:
        raise HTTPException(status_code = 404, detail = "No account found with id {}".format(username))
    else:
        return record


@router.get("/api/accounts", response_model = AccountListOut)
def get_accounts(
    queries: AccountQueries = Depends()
):

    return {"accounts": queries.get_all_accounts()}


# @router.post("/api/accounts", response_model=AccountOut)
# def create_account(
#     account: AccountIn,
#     queries: AccountQueries = Depends(),
# ):
#     try:
#         return queries.create_account(account)
#     except ForeignKeyViolation as e:
#         raise HTTPException(status_code = 400)



@router.post("/api/accounts", response_model=AccountToken | HttpError)
async def create_account(
    data: AccountIn,
    request: Request,
    response: Response,
    accounts: AccountQueries = Depends(),
):
    hashed_password = authenticator.hash_password(data.password)
    try:
        account = accounts.create_account(data, hashed_password)
    except DuplicateAccountError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create an account with those credentials",
        )
    form = AccountForm(username=data.email, password=data.password)
    token = await authenticator.login(response, request, form, accounts)
    return AccountToken(account=account, **token.dict())