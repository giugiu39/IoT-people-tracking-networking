import time
import json
import argparse
# import ble_client logic or coap_client logic here depending on the test

def generate_dummy_event(event_id):
    return {
        "event_id": event_id,
        "person_id": 999,
        "from_zone": "Zone_A",
        "to_zone": "Zone_B",
        "ts_send_ns": time.time_ns(),
        "confidence": 0.85
    }

def run_load_test(rate_hz, duration_sec, protocol):
    total_events = rate_hz * duration_sec
    delay_between_events = 1.0 / rate_hz

    print(f"Starting {protocol} Load Test: {rate_hz} Hz for {duration_sec}s ({total_events} events)")

    for i in range(total_events):
        start_time = time.time()
        event = generate_dummy_event(i)
        payload = json.dumps(event)
        
        if protocol == "MQTT":
            pass # TODO: Insert MQTT publish or BLE characteristic write here
        elif protocol == "CoAP":
            pass # TODO: Insert CoAP POST request here
            
        elapsed = time.time() - start_time
        sleep_time = delay_between_events - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rate", type=int, default=10, help="Events per second")
    parser.add_argument("--duration", type=int, default=30, help="Duration in seconds")
    parser.add_argument("--protocol", choices=["MQTT", "CoAP"], default="MQTT")
    args = parser.parse_args()
    
    run_load_test(args.rate, args.duration, args.protocol)