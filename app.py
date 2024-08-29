import streamlit as st
from msfabricpysdkcore import FabricAzureClient
import pandas as pd
import os
import jwt

offline_mode = False

if offline_mode:
    import dotenv
    dotenv.load_dotenv(".env")

tenant_id = os.getenv("TENANT_ID")
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
subscriptions = os.getenv("SUBSCRIPTIONS")

subscriptions = subscriptions.split(",")
subscriptions = set(subscriptions)

fac = FabricAzureClient(tenant_id=tenant_id, client_id=client_id, client_secret=client_secret)

st.title('Hello, Fabric Capacity Admin!')
st.write('Welcome to your Fabric Capacity admin app.')





if offline_mode:
    user_name = "John Dummy"
    user_mail = "admin@MngEnvMCAP065039.onmicrosoft.com"
else:
    user_name = st.context.headers["X-Ms-Client-Principal-Name"]

    token = st.context.headers["X-Ms-Token-Aad-Access-Token"]
    decoded = jwt.decode(token, options={"verify_signature": False}) # works in PyJWT >= v2.0
    user_mail = decoded["upn"]

st.write(f"Logged in user: {user_name}")
st.write(f"User email: {user_mail}")

# Select box
capacities = list()
for sub in subscriptions:
    capacities.extend(fac.list_by_subscription(sub))
capas_dict_list = list()
for cap in capacities:
    capa = dict()
    capa["name"] = cap["name"]
    capa["state"] = cap["properties"]["state"]
    capa["sku"] = cap["sku"]["name"]
    capa["subscription"] = cap["id"].split("/")[2]
    capa["resource_group"] = cap["id"].split("/")[4]
    capa["admins"] = cap["properties"]["administration"]["members"]

    capas_dict_list.append(capa)
capas_user = [capa for capa in capas_dict_list if user_mail in capa["admins"]]


if capas_user == []:
    st.write("You are not an admin of any capacity.")
else:
    st.write('\n\n\n\nThis is the list of capacities for which you are an admin:')

    df = pd.DataFrame(capas_user)


    capa_names = df["name"].tolist()

    # Display the table
    st.table(df)

    capa_name = st.multiselect(
        'Choose a capacity',
        capa_names
    )
    st.write(f'You selected:\n\n{capa_name}')

    option = st.selectbox(
        'Choose an action',
        ["Resume", "Suspend", "Scale"]
    )
    #st.write(f'You selected: {option}')

    if option == "Scale":
        scale = st.selectbox(
        'Choose an SKU',
        ["F2", "F4", "F8", "F16", "F32", "F64", "F128", "F256", "F512", "F1024", "F2048"]
    )


    # Button
    if st.button('Execute'):
        for cap_ in capa_name:
            capa = [cap for cap in capas_user if cap["name"] == cap_][0]

            if option == "Resume":
                fac.resume_capacity(capa["subscription"], capa["resource_group"], capa["name"])
            elif option == "Suspend":
                fac.suspend_capacity(capa["subscription"], capa["resource_group"], capa["name"])
            elif option == "Scale":
                fac.update_capacity(capa["subscription"], capa["resource_group"], capa["name"], sku=scale)
        st.rerun()

if st.button('Refresh'):
    st.rerun()



