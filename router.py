from fastapi import APIRouter,Depends,Path
from fastapi import HTTPException
from model import LoginRequest,OTPRequest,WatchlistName,WatchlistNameUpdate,InsertStocks,SearchStock
from db import users,tokenData,watchlist,stocks
from tokenDetails import create_access_token
from datetime import datetime
import re,random
global gmail  
user=APIRouter() 
#token_Display() returns the JWT token that is stored in the token database.
def token_Display():
    try:
      global gmail
      logout_user= users.find_one({"email":gmail})              
      otp_user=tokenData.find_one({"user_id":logout_user['_id']})  
      token_return=otp_user['accessToken']
      return token_return
    except Exception as e:
        raise HTTPException(status_code=400, detail="Could not validate credentials") 
#get_next_id() creates a unique ID for the Watchlist
def get_next_id():
    last_id = watchlist.find_one(sort=[("id", -1)])
    if last_id:
        return last_id["id"] + 1
    return 1
#Login Endpoint
@user.post("/login",tags=["Login"])
async def login(login: LoginRequest):                                         
    global gmail                                                              
    try:                                                                      
        #Checks whether the email address format is valid or not.
        if not login.email:
            raise HTTPException(status_code=400,detail="Email is required")             
        if not re.match(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$',login.email):    
             raise HTTPException(status_code=400, detail="Email Invalid")     
        login_user = users.find_one({"email":login.email})                  
        gmail=login.email                                                    
        #Generates a Four digit OTP.                                          
        OTP=random.randint(1000,9999)                                         
        login_date=datetime.now()  
        #Checks if the user is found in the database or not.                                          
        if login_user: 
           #Updates user related information if found.                                                       
           login_user= tokenData.find_one({"user_id":login_user['_id']})
           users.update_one({"_id":login_user['_id']}, {"$set": {"email":login.email,"Created_At":login_date}})
           access_token =create_access_token(data={"sub":login.email})
           tokenData.update_one({"_id":login_user['_id']},{"$set":{"OTP":OTP,"accessToken":access_token}}) 
        else:  
           #Inserts information about the user into the database if not found               
           users.insert_one({"email":login.email,"accessTokenLogin":None,"Created_At":login_date})  
           login_user= users.find_one({"email":login.email})
           access_token =create_access_token(data={"sub":login.email})
           tokenData.insert_one({"user_id":login_user['_id'],"OTP":OTP,"accessToken":access_token})  
        return {"token":access_token}
    except Exception as e:
        raise e
#OTP Endpoint
@user.post("/otp",tags=["Login"])
async def OtpVerification(request:OTPRequest):
    try: 
       otp_user=tokenData.find_one({"accessToken":request.token})                    
       #Checks if the JWT token in the token database is None                                    
       if not request.token:                                              
          raise HTTPException(status_code=400, detail="Token is required")  
       if not request.OTP:                                              
          raise HTTPException(status_code=400, detail="OTP is required")    
       Otp_length=str(request.OTP)                                                                                                                          
       #checking length of the OTP                                                                                                                                  
       if len(Otp_length)!=4:                                                       
            raise HTTPException(status_code=400, detail="Invalid OTP Length")
       #They check if the OTP entered by the user matches in the database.
       if otp_user['OTP']==request.OTP:
         oto_login_user=users.find_one({"_id":otp_user['user_id']})  
         access_token =create_access_token(data={"sub":oto_login_user['email']})
         users.update_one({"_id":otp_user['user_id']}, {"$set": {"accessTokenLogin":access_token}})
         return {"token":access_token}                 
       else:
          raise HTTPException(status_code=400, detail=" InCorrect OTP")
    except Exception as e:
         raise e   
@user.post("/watchlists",tags=["Login"])
async def watchlistInsert(name:WatchlistName,token_return:str=Depends(token_Display)):
    try:                                                                               
       login_user= tokenData.find_one({"accessToken":token_return})                        
       find_user=users.find_one({"_id":login_user['user_id']})                          
       #Checks if the JWT token in the login database is null                           
       if find_user["accessTokenLogin"] is None:                                        
           raise HTTPException(status_code=400,detail="Could not validate credentials") 
        #Checks whether the Watchlist Name entered by the user is empty or not                                               
       if not name.name:                                  
           raise HTTPException(status_code=400,detail="WatchlistName Is Empty")         
       #Check if the user has entered a watchlist name and                              
     #if it already exists in the database under that particular user then throw error.           
       watchlistname_find= watchlist.find_one({"user_id":login_user['user_id'],"name":name.name})
       if watchlistname_find:
           raise HTTPException(status_code=400,detail="This name is already exits!!! Enter another name.") 
       watchlistname_find= watchlist.find_one({"user_id":login_user['user_id'],"name":{"$regex":f"^{name.name}$","$options":"i"}})
       if watchlistname_find:
           if str(watchlistname_find["name"]).lower()==name.name.lower():
                raise HTTPException(status_code=400,detail="This name is already exits!!! Enter another name.")                                     
       id=get_next_id()
       #Insert Watchlist Name in database
       watchlist.insert_one({"id":id,"name":name.name,"user_id":login_user['user_id'],"stocks":[]})  
       watchlistname_find= watchlist.find_one({"user_id":login_user['user_id'],"name":name.name})
       if watchlistname_find:
           return{"status":"success","message":'Watchlist created successfully',"watchlist_id":watchlistname_find['id']}
    except Exception as e:
         raise e
@user.delete("/watchlists/{watchlist_id}",description="Delete watchlist")
async def watchlistDelete(watchlist_id:int,token_return:str=Depends(token_Display)):
    try:                                                                                
        login_user= tokenData.find_one({"accessToken":token_return})                        
        find_user=users.find_one({"_id":login_user['user_id']})                        
        #Checks if the JWT token in the login database is null                          
        if find_user["accessTokenLogin"] is None:                                       
           raise HTTPException(status_code=400,detail="Could not validate credentials")             
        watchlistname_find= watchlist.find_one({"user_id":login_user['user_id'],"id":watchlist_id})
       #check whether the watchlist Id present in the database or not.if it is present then delete it.
        if watchlistname_find:
            watchlist.delete_one({"id":watchlistname_find['id']})
            return{"status":'success',"message":"Watchlist deleted successfully"}
        else:
            raise HTTPException(status_code=400,detail="Watchlist Not Found")                       
    except Exception as e:
        raise e
@user.put("/watchlists/{watchlist_id}",tags=["Login"])
async def watchlistnameUpdate(watchlist_id:int,name:WatchlistNameUpdate,token_return:str=Depends(token_Display)):
    try:
       login_user= tokenData.find_one({"accessToken":token_return})                       
       find_user=users.find_one({"_id":login_user['user_id']})                         
       #Checks if the JWT token in the login database is null                           
       if find_user["accessTokenLogin"] is None:                                        
           raise HTTPException(status_code=400,detail="Could not validate credentials") 
        #Checks whether the Watchlist Name entered by the user is empty or not                            
       if not name.name:
           raise HTTPException(status_code=400,detail="WatchlistName Is Empty")
       watchlistname_find= watchlist.find_one({"user_id":login_user['user_id'],"name":name.name})
       if watchlistname_find:
           raise HTTPException(status_code=400,detail="This name is already exits!!! Enter another name.") 
       if watchlistname_find:
           if str(watchlistname_find["name"]).lower()==name.name.lower():
                raise HTTPException(status_code=400,detail="This name is already exits!!! Enter another name.")                                                              
       watchlistname_find= watchlist.find_one({"user_id":login_user['user_id'],"id":watchlist_id})
       #check whether the watchlist Id present in the database or not.if it is present then update it.
       if watchlistname_find:
           watchlist.find_one_and_update({"id":watchlist_id},{"$set":{"name":name.name}})
           return{"status":"success","message":"Watchlist updated successfully"}
       else:
           raise HTTPException(status_code=400,detail="Watchlist Not Found.")                                
    except Exception as e:
        raise e
@user.get("/watchlists",description="Get list of watchlist")
async def watchlistsDisplay(token_return:str=Depends(token_Display)):
    try:
       login_user= tokenData.find_one({"accessToken":token_return})
       find_user=users.find_one({"_id":login_user['user_id']})                         
       #Checks if the JWT token in the login database is null                          
       if find_user["accessTokenLogin"] is None:                                       
           raise HTTPException(status_code=400,detail="Could not validate credentials")             
       if not login_user:                                                              
            raise HTTPException(status_code=400,detail="Invalid Authenticate Token.") 
       watchlistname_find= watchlist.find_one({"user_id":login_user['user_id']})
       n=watchlist.count_documents({})
       if n==0:
           raise HTTPException(status_code=400,detail="Watchlist is Empty.")       
       if  "stocks" not in watchlist.find_one(): 
           watchlists=[]
           for list in watchlist.find({"user_id":login_user["user_id"]}):
              watchlists.append({"name": list["name"], "id":list["id"]})
           return watchlists                                           
       watchlists=[]
       for list in watchlist.find({"user_id":login_user["user_id"]}):
            stocks = []
            for stock in list["stocks"]:
                # Retrieve the stock data from the watchlist database
                stock_data = {"symbol": stock["symbol"], "token": stock["token"]}
                stocks.append(stock_data)
            watchlists.append({"name": list["name"], "id":list["id"], "stocks": stocks})
       return watchlists                                             
    except Exception as e:
        raise e
@user.post("/watchlists/stocks",description="Searching Stock")
async def searchingStock(symbol:SearchStock,token_return:str=Depends(token_Display)):
    try:
        if not symbol.symbol:
            raise HTTPException(status_code=400,detail="Trading Symbol name is empty")  
        if not re.match(r'^[a-zA-Z]+$',symbol.symbol): 
            raise HTTPException(status_code=400,detail="Trading Symbol name is not in string format")             
        results = []
        regex = f'^{symbol.symbol}'
        stock=[]
        count=0
        for stock in stocks.find({'Trading Symbol': {'$regex': regex, '$options': 'i'}}):
           name = stock['Name']
           symbol = stock['Trading Symbol']
           token = stock['Instrument Token']
           tick_size = stock['Tick Size']
           data = {
            "Name": name,
            "Trading Symbol": symbol,
            "Instrument Token": token,
            "Tick Size": tick_size,
           }
           count=count+1
           results.append(data)
        if count>0:
           return results
        else:
            raise HTTPException(status_code=400,detail="Trading Symbol not found")     
    except Exception as e:
        raise e
@user.put("/watchlists/{watchlist_id}/stocks",description="Add stock to watchlist")
async def insertStockInWatchlist(watchlist_id:int,stock:InsertStocks,token_return:str=Depends(token_Display)):
    try:                                                                                              
        login_user= tokenData.find_one({"accessToken":token_return})                                     
        find_user=users.find_one({"_id":login_user['user_id']})                                        
        #Checks if the JWT token in the login database is null                                        
        if find_user["accessTokenLogin"] is None:                                                      
           raise HTTPException(status_code=400,detail="Could not validate credentials")           
        #Checks whether the symbol entered by the user is empty or not                               
        if not stock.symbol:                                           
           raise HTTPException(status_code=400,detail="Symbol Is Empty") 
        if not stock.token:                                           
           raise HTTPException(status_code=400,detail="Token Is Empty")                             
        watchlistname_id_find= watchlist.find_one({"user_id":login_user['user_id'],"id":watchlist_id})
        #Check whether the stock is already present in database or not.
        watchlistmatch_id_token= watchlist.find_one({"id":watchlistname_id_find['id'],"stocks.token":stock.token})
        if watchlistmatch_id_token:
            raise HTTPException(status_code=400,detail="Stock already present in watchlists.") 
        #insert stock in that particular Watchlist if the watchlist is present under that user                           
        if watchlistname_id_find:   
              watchlist.find_one_and_update({"id":watchlist_id},{"$push":{"stocks":{'$each':[{"symbol": stock.symbol, "token": stock.token}]}}})
              return{"status":"success","message":"Stock Added to Watchlist successfully"}                               
    except Exception as e:
        raise e
@user.delete("/watchlists/{watchlist_id}/{token}")
async def deleteStock(watchlist_id:int,token:int,token_return:str=Depends(token_Display)):
    try:                                                                                       
        login_user= tokenData.find_one({"accessToken":token_return})                              
        find_user=users.find_one({"_id":login_user['user_id']})                                  
        #Checks if the JWT token in the login database is null                                  
        if find_user["accessTokenLogin"] is None:                                               
           raise HTTPException(status_code=400,detail="Could not validate credentials")                
        watchlistmatch_id_token= watchlist.find_one({"id":watchlist_id,"stocks.token":token})    
        #check if the token Id found or not
        if not watchlistmatch_id_token:
            raise HTTPException(status_code=400,detail="Inavlid Token ID")
        # delete symbol and token from watchlist             
        result =watchlist.update_one({"id": watchlist_id},{"$pull": {"stocks": {"token": token}}})
        if result:
              return{"status":"success","message":"Stock Deleted from Watchlist successfully"}               
    except Exception as e:
        raise e   
@user.get("/logout",tags=["Login"])
async def logout(token_return:str=Depends(token_Display)):
    try:
      global gmail                                                                    
      login_user= tokenData.find_one({"accessToken":token_return})                       
      find_user=users.find_one({"_id":login_user['user_id']})                         
      #Checks if the JWT token in the login database is null                                                                               
      if find_user["accessTokenLogin"] is None:                                       
         raise HTTPException(status_code=400,detail="Could not validate credentials")                                                                  
      #check if the user is found or not 
      if find_user:                                        
         users.update_one({"_id":find_user['_id']}, {"$set": {"accessTokenLogin":None}})
         tokenData.update_many({"user_id":find_user['_id']},{"$set": {"OTP":None}})
         gmail=None
         return{"message":"Logout Succesfully"}
      else:
         raise HTTPException(status_code=400, detail="User Not Found")
    except Exception as e:
        raise e


       

