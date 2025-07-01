## Start the Test Server (in terminal):

```bash
python tcp_test_server.py
```

(Default: runs on port 8080)

#### 2. In the GUI Tool:

1. Switch to "TCP Test" tab  
2. Enter:  
   - IP: `127.0.0.1` (for local testing)  
   - Port: `8080`  
3. Buttons:  
   - **Test Connection**: Checks basic connectivity  
   - **Send Data**: Sends custom text and shows server reply  

#### 3. Expected Output:

- Server echoes all messages with timestamp  
- Example:  
  You send: `hello`  
  Server replies: `ECHO[1623456789]: hello`  


