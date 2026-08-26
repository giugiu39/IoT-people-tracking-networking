import asyncio
import json
import time
import aiocoap

async def main():
    print("Avvio CoAP Client Simulator (Nodo Edge)...")
    
    # Crea il contesto di rete del client
    context = await aiocoap.Context.create_client_context()
    
    # Indirizzo del server (se giri tutto sul Mac usa 127.0.0.1)
    # Quando passerai al Raspberry, metterai l'IP Wi-Fi del tuo Mac (es. 192.168.1.50)
    server_uri = "coap://127.0.0.1/tracking"
    
    # Prepariamo un payload finto identico a quello che genererebbe YOLO
    event_data = {
        "person_id": 13,
        "event": "Zone_C -> Zone_B",
        "timestamp": time.time()  # Timestamp esatto di generazione!
    }
    
    payload = json.dumps(event_data).encode('utf-8')
    
    # Costruiamo il pacchetto CoAP. 
    # mtype=aiocoap.CON significa "Confirmable" (richiede l'ACK del server)
    # mtype=aiocoap.NON significa "Non-Confirmable" (spara e dimentica, più veloce ma non sicuro)
    request = aiocoap.Message(code=aiocoap.POST, 
                              payload=payload, 
                              uri=server_uri,
                              mtype=aiocoap.CON) 
    
    try:
        print(f"Spedizione pacchetto per Persona {event_data['person_id']} in corso...")
        
        # Invia il messaggio e attendi la risposta
        response = await context.request(request).response
        print(f"Risposta ricevuta dal Server: {response.code} -> {response.payload.decode('utf-8')}")
        
    except Exception as e:
        print(f"Timeout o errore di rete: {e}")

if __name__ == "__main__":
    asyncio.run(main())