from fastapi import FastAPIRouter

userModel = {
    user_id,
    name,
    email,
    phone_number,
    street1,
    street2
}

userResponse = {
    user_id: "Data",
    name:  "Data",
    email: "Data",
    phone_number: "Data",
    street1: "Data",
    street2: "Data"
}

@router.post("/update_user", response_model=userResponse)
async def assess(payload: userModel) -> userResponse:

    #SQL query to update user or create if doesnt exsist

    return userResponse
    

@router.delete("/delete_user", response_model=True_False)
async def assess(payload: userModel) -> True_False:

    #SQL query to delete user
    
    return True / False


@router.post("/get_user", response_model=userResponse)
async def assess(payload: user_id) -> userResponse:

    #SQL query to get user
    
    return userResponse