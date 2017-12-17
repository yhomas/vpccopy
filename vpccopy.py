import requests as rq
import json
import copy
from time import sleep
from optparse import OptionParser

############## set the json keys which are output only ##############
DelListNetwork =["creationTimestamp", "id", "kind", "peerings", "selfLink", "subnetworks"]
DelListSubnetwork =["creationTimestamp", "gatewayAddress", "id", "kind", "selfLink", "region"]
DelListFirewalls =["creationTimestamp", "id", "kind", "selfLink"]
DelListRoutes =["creationTimestamp", "id", "kind", "selfLink", "warnings", "nextHopNetwork"]

def postRequest(RequestURL, RequestDict, TargetComponents):
    print "Now Creating "+RequestDict["name"]+" "+TargetComponents+"...",
    while True:
        r=rq.post(RequestURL, data=json.dumps(RequestDict), headers=POSTrequestHeader)
        sleep(1)
        try:
            if json.loads(str(r.text))["error"]["errors"][0]["reason"] == "resourceNotReady":
                continue
            else:
                print("skip: "+json.loads(str(r.text))["error"]["message"])
                break

        except KeyError:
            print("success")
            break

def ConvertNetwork(DelListNetwork, DelListSubnetwork, Options):
    OldProject=Options.SourceProject
    NewProject=Options.DestinationProject
    ######### Global Networks ###########
    OldProjectGlobalNetworks='https://www.googleapis.com/compute/v1/projects/'+OldProject+'/global/networks'
    NewProjectGlobalNetworks='https://www.googleapis.com/compute/v1/projects/'+NewProject+'/global/networks'
    
    r=rq.get(OldProjectGlobalNetworks, headers=GETrequestHeader)

    Oldinit_dict=json.loads(str(r.text))
    Newinit_dict=json.loads(str(r.text.replace(OldProject,NewProject)))
    for NumNetwork in range(len(Newinit_dict["items"])):
        RequestDict=copy.deepcopy(Newinit_dict["items"][NumNetwork])


        for DelElm in DelListNetwork:
            try:
                popVal = RequestDict.pop(DelElm)
            except KeyError:
                continue

        postRequest(NewProjectGlobalNetworks, RequestDict, "Global Networks")

        ######## Subnetworks ##########

        subnetworkArray=Oldinit_dict["items"][NumNetwork]["subnetworks"]
        NewsubnetworkArray=Newinit_dict["items"][NumNetwork]["subnetworks"]


        for (EachNewSubnetwork, EachSubnetwork) in zip(NewsubnetworkArray, subnetworkArray):
            r=rq.get(EachSubnetwork, headers=GETrequestHeader)
            RequestDict=json.loads(str(r.text.replace(OldProject,NewProject)))
            RequestSubnetURL=EachNewSubnetwork.replace("/"+RequestDict["name"], "")
            for DelElm in DelListSubnetwork:
                try:
                    popVal = RequestDict.pop(DelElm)
                except KeyError:
                    continue

            postRequest(RequestSubnetURL, RequestDict, "subnetworks")

######## Firewall and Routes ############

def Convertcomponents(components, DelList, Options):
    OldProject=Options.SourceProject
    NewProject=Options.DestinationProject
    OldProjectGlobalComponent='https://www.googleapis.com/compute/v1/projects/'+OldProject+'/global/'+components
    NewProjectGlobalComponent='https://www.googleapis.com/compute/v1/projects/'+NewProject+'/global/'+components

    r=rq.get(OldProjectGlobalComponent, headers=GETrequestHeader)

    Oldinit_dict=json.loads(str(r.text))
    Newinit_dict=json.loads(str(r.text.replace(OldProject,NewProject)))

    for (EachNewComponentRule, EachComponentRule) in zip(Newinit_dict["items"], Oldinit_dict["items"]):
        RequestDict=copy.deepcopy(EachNewComponentRule)
        for DelElm in DelList:
            try:
                popVal = RequestDict.pop(DelElm)
            except KeyError:
                continue

        postRequest(NewProjectGlobalComponent, RequestDict, components)

def ConvertExecution(Options):
        print("\n************CONFIRMATION************")
        print("Source Project ID: "+Options.SourceProject)
        print("Destination Project ID: "+Options.DestinationProject)
        print("************************************\n")
        print("Note: If destination project has the same name component, the component is skipped.")
        flag=raw_input("VPC network setting is about to copy. Continue?(Y/n)")
        
        if flag == "y" or flag == "Y" or flag == "":
            try:
                requestHeader = {"Metadata-Flavor" : "Google"}
                r=rq.get('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token', headers=requestHeader)
                init_dict=str(r.text)
                access_token=str(init_dict["access_token"])

            except:
                if Options.AccessToken == None:
                    print("This script should run on google cloud shell. If you want to use this on others, give your access token by using option \"-t\".")
                    print("You can get your access token \"gcloud auth application-default print-access-token\" command.")
                    return

                else:
                    access_token=Options.AccessToken
            
            global GETrequestHeader
            global POSTrequestHeader
            GETrequestHeader = {"Authorization":"Bearer "+access_token}
            POSTrequestHeader = {"Authorization":"Bearer "+access_token, "Content-Type" : "application/json"}
            ConvertNetwork(DelListNetwork, DelListSubnetwork, Options)
            Convertcomponents("firewalls", DelListFirewalls, Options)
            Conovertcomponents("routes", DelListRoutes, Options)

        else:
            print("The process has been stopped")

def main():
    usage = "usage: %prog [options]"
    parser = OptionParser(usage)
    parser.add_option("-s", "--sourceProject", dest = "SourceProject", action = "store",
                        help = "source project ID of which you want to copy VPC network")
    parser.add_option("-d", "--destProject", dest = "DestinationProject", action = "store",
                        help = "destination project ID of which you want to copy VPC network")
    parser.add_option("-t", "--token", dest = "AccessToken", action = "store",
                        help = "Your access token from \"gcloud auth application-default print-access-token\".")

    (options, args) = parser.parse_args()
    if options.SourceProject == None or options.DestinationProject == None:
        parser.error("Input source and destination project ID. Confirm the usage by using option \"-h\".")
    else:
        ConvertExecution(options)

if __name__ == '__main__':
    main()
