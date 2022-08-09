import simpleobsws
import asyncio

parameters = simpleobsws.IdentificationParameters(ignoreNonFatalRequestChecks = False)
ws = simpleobsws.WebSocketClient(url = 'ws://localhost:4444',
                                  identification_parameters = parameters)

loop = asyncio.get_event_loop()
async def make_request():
  await ws.connect()
  print('connected')
  await ws.wait_until_identified()
  request = simpleobsws.Request('GetRecordStatus') # StopRecord for stopping
  

  ret = await ws.call(request) # Perform the request
  if ret.ok(): # Check if the request succeeded
    print("Request succeeded!")
    return ret.responseData
  else:
    print(ret)
  print('finish')
    

result = loop.run_until_complete(make_request())['outputActive']
print(result)