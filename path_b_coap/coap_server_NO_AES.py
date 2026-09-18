import asyncio
import json
import time
import os
import aiocoap
import aiocoap.resource as resource

# Assicuriamoci che la cartella di output esista
os.makedirs("edge_ai/output", exist_ok=True)


class TrackingResource(resource.Resource):

    def __init__(self):
        super().__init__()
        self.message_count = 0

    async def render_post(self, request):
        receive_time_ns = time.time_ns()
        self.message_count += 1

        try:
            # 1. Parsing diretto del JSON dai byte grezzi ricevuti (NO_AES)
            raw_payload = request.payload
            
            event_data = json.loads(
                raw_payload.decode("utf-8")
            )

            # 2. Timestamp generato dal Raspberry
            send_time_ns = event_data.get(
                "ts_send_ns",
                receive_time_ns
            )

            # 3. Latenza end-to-end reale
            #    Raspberry -> Mac
            raw_diff_ns = receive_time_ns - send_time_ns
            latency_ms = raw_diff_ns / 1_000_000.0

            # 4. Rimuove eventuale confidence dal JSON
            event_data.pop("confidence", None)

            event_data["path"] = "CoAP_NO_AES"
            event_data["latency_ms"] = round(latency_ms, 3)

            # 5. Salvataggio evento sul file di baseline NO_AES
            with open(
                "edge_ai/output/events_NO_AES.jsonl",
                "a"
            ) as f:
                f.write(
                    json.dumps(event_data) + "\n"
                )

            person_id = event_data.get(
                "person_id",
                "Unknown"
            )
            from_z = event_data.get(
                "from_zone",
                "?"
            )
            to_z = event_data.get(
                "to_zone",
                "?"
            )

            print(
                f"[Msg #{self.message_count}] "
                f"Person {person_id}: "
                f"{from_z} -> {to_z} | "
                f"Latenza: {latency_ms:.3f} ms"
            )

            return aiocoap.Message(
                code=aiocoap.CHANGED,
                payload=b"ACK: Event processed"
            )

        except Exception as e:
            print(
                f"Errore nel parsing del payload in chiaro: {e}"
            )

            return aiocoap.Message(
                code=aiocoap.BAD_REQUEST
            )


async def main():
    root = resource.Site()

    root.add_resource(
        ["tracking"],
        TrackingResource()
    )

    print("=======================================")
    print(" CoAP Server in avvio (PATH B - NO_AES)")
    print(" In ascolto su coap://192.168.1.151:5683/tracking")
    print("=======================================")

    await aiocoap.Context.create_server_context(
        root,
        bind=("192.168.1.151", 5683)
    )

    await asyncio.get_running_loop().create_future()


if __name__ == "__main__":
    asyncio.run(main())