
from lynkr.client import LynkrClient


if __name__ == "__main__":

    client = LynkrClient("sk_99861890cbfae785144c5f3a7dcfc71a8ef6723b42cdbe3dc32c2a3a2ef3d6af")

    schemaResponse = client.get_schema("I want to send an email")

    
    schema = {
    "x-api-key":      "re_pQJPXSF5_AtMuQDc3dstXi7q2eJYBadA6",
    "sender_address": "noreply@lynkr.ca",
    "receiver_address":"batuhanaktan@gmail.com",
    "subject":        "hello",
    "html":           "<p>hello</p>",
    }


    response = client.execute_action(schema_data=schema)

    print(response)