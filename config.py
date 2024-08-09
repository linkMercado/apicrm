APPNAME = "api_crm"

LogConfig = {
  "appname": APPNAME, 
  "logfilename": "varlogapis.log"
}

DbConfig = {
          "host": "172.31.40.103" 
        , "user": "LMercado"
        , "port": "3306"
        , "password": "!nt3rn3tf@st"
        , "autocommit": True
        , "database": "linkmercado"
        , "pool_size": 5
        , "max_pool_size": 10
        , "pool_name": "CRM-LMPool"
}