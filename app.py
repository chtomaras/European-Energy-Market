from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
import xmltodict
from datetime import datetime, timedelta

def transform_data(array):
    out_arr = []
    i = 0
    for key in array.keys():
        out_arr.append(array[key].split("-")[::-1])
        out_arr[i][1] = array[key].split("-")[::-1][2]
        out_arr[i][2] = array[key].split("-")[::-1][1]
        out_arr[i] = "-".join(out_arr[i])
        i += 1
    return out_arr

def timeline_transform(array, interval):
    output = []
    
    # Transform Data & Labels
    data_points = []
    labels=[]
    for i in range(int(len(array[0])/interval)):
        data_points.append(sum(array[0][i*interval:(i+1)*interval])/interval)
        if( interval >= 24):
            labels.append(array[1][i*interval][:(len(array[1][i*interval])-5)])
        else:
            labels.append(array[1][i*interval])
    output.append(data_points)
    output.append(labels)
    output.append(max(data_points))
    output.append(min(data_points))
    
    #Standar Deviation
    sqrSum = 0
    for value in data_points:
        sqrSum += pow(value - array[4], 2)
    
    output.append(array[4])
    output.append(pow(sqrSum/len(data_points),0.5))
    return output

app = Flask(__name__)
CORS(app)
app.testing = True

@app.route("/")
def main():
    return render_template('html/index.html')

@app.route("/compute/different-time-country")
def one_country_different_time():
    return render_template('html/different-time-country.html')

@app.route("/compute/different-country")
def different_country():
    return render_template('html/different-country.html')

@app.route("/compute/one-country")
def one_country():
    return render_template('html/one-country.html')

@app.route("/getRegionData", methods=['POST'])
def get_region_data():
    data = request.json
    output = []
    timeline = data["timeline"]
    for region in data["data"]:
        data = request.json
        pair = {
            "start_date": data['time'][0],
            "end_date": data['time'][1]
        }
        pair = transform_data(pair)
        start_date = f"{pair[0]}T00:00Z"
        end_date = f"{pair[1]}T00:00Z"
        headers = {
            "Content-Type": "application/xml",
            "Accept": "*/*",
            "Accept-Encoding": "gzip,deflate,br",
            "Connection": "keep-alive",
            "SECURITY_TOKEN": "7eb90cca-a5bf-407b-aa88-ae29a2bb3fe2"
            }
        xml = f"""
        <StatusRequest_MarketDocument xmlns="urn:iec62325.351:tc57wg16:451-5:statusrequestdocument:4:0">
        <mRID>SampleCallToRestfulApi</mRID>
        <type>A59</type>
        <sender_MarketParticipant.mRID codingScheme="A01">10X1001A1001A450</sender_MarketParticipant.mRID>
        <sender_MarketParticipant.marketRole.type>A07</sender_MarketParticipant.marketRole.type>
        <receiver_MarketParticipant.mRID codingScheme="A01">10X1001A1001A450</receiver_MarketParticipant.mRID>
        <receiver_MarketParticipant.marketRole.type>A32</receiver_MarketParticipant.marketRole.type>
        <createdDateTime>2016-01-10T13:00:00Z</createdDateTime>
        <AttributeInstanceComponent>
            <attribute>DocumentType</attribute>
            <attributeValue>A44</attributeValue>
        </AttributeInstanceComponent>
        <AttributeInstanceComponent>
            <attribute>In_Domain</attribute>
            <attributeValue>{region}</attributeValue>
        </AttributeInstanceComponent>
        <AttributeInstanceComponent>
            <attribute>Out_Domain</attribute>
            <attributeValue>{region}</attributeValue>
        </AttributeInstanceComponent>
        <AttributeInstanceComponent>
            <attribute>ProcessType</attribute>
            <attributeValue>A01</attributeValue>
        </AttributeInstanceComponent>
        <AttributeInstanceComponent>
            <attribute>TimeInterval</attribute>
            <attributeValue>{start_date}/{end_date}</attributeValue>
        </AttributeInstanceComponent>
        </StatusRequest_MarketDocument> 
        """
        
        # Get Data
        data = requests.post('https://web-api.tp.entsoe.eu/api', data=xml, headers=headers).text
        print(data);
        data = xmltodict.parse(data)["Publication_MarketDocument"]["TimeSeries"]
        points = []
        
        #Create Time Point
        time = datetime.strptime(start_date, "%Y-%m-%dT%H:%MZ")
        
        #Loop Through Points
        for Object in data:
            points = points + Object["Period"]["Point"]
        
        #Data to return
        formatedData = [[],[]]
        avg = 0
        
        #Store Points
        for i,point in enumerate(points):
            formatedData[0].append(float(point["price.amount"]))
            formatedData[1].append(time.strftime("%d/%m/%Y %H:%M"))
            time = time + timedelta(hours=1)
        
        #Calculate Measurements
        avg = sum(formatedData[0])/len(formatedData[0])
        
        formatedData.append(max(formatedData[0]))
        formatedData.append(min(formatedData[0]))
        # formatedData.append([avg for x in range(len(formatedData[0]))])
        formatedData.append(avg)
        
        #Standar Deviation
        sqrSum = 0
        for value in formatedData[0]:
            sqrSum += pow(value - avg, 2)
        formatedData.append(pow(sqrSum/len(formatedData[0]),0.5))
        formatedData = timeline_transform(formatedData, int(timeline))
        output.append(formatedData)
    return jsonify({"data": output})

@app.route("/getdata", methods=['POST'])
def get_data():
    output = []
    data = request.json
    timeline = data["timeline"]
    for time_pair in data["data"]:
        pair = {
            "start_date": time_pair[0],
            "end_date": time_pair[1]
        }
        pair = transform_data(pair)
        start_date = f"{pair[0]}T00:00Z"
        end_date = f"{pair[1]}T00:00Z"
        headers = {
            "Content-Type": "application/xml",
            "Accept": "*/*",
            "Accept-Encoding": "gzip,deflate,br",
            "Connection": "keep-alive",
            "SECURITY_TOKEN": "YOUR_ENTSOE_TOKEN_HERE"
            }
        xml = f"""
        <StatusRequest_MarketDocument xmlns="urn:iec62325.351:tc57wg16:451-5:statusrequestdocument:4:0">
        <mRID>SampleCallToRestfulApi</mRID>
        <type>A59</type>
        <sender_MarketParticipant.mRID codingScheme="A01">10X1001A1001A450</sender_MarketParticipant.mRID>
        <sender_MarketParticipant.marketRole.type>A07</sender_MarketParticipant.marketRole.type>
        <receiver_MarketParticipant.mRID codingScheme="A01">10X1001A1001A450</receiver_MarketParticipant.mRID>
        <receiver_MarketParticipant.marketRole.type>A32</receiver_MarketParticipant.marketRole.type>
        <createdDateTime>2016-01-10T13:00:00Z</createdDateTime>
        <AttributeInstanceComponent>
            <attribute>DocumentType</attribute>
            <attributeValue>A44</attributeValue>
        </AttributeInstanceComponent>
        <AttributeInstanceComponent>
            <attribute>In_Domain</attribute>
            <attributeValue>10YGR-HTSO-----Y</attributeValue>
        </AttributeInstanceComponent>
        <AttributeInstanceComponent>
            <attribute>Out_Domain</attribute>
            <attributeValue>10YGR-HTSO-----Y</attributeValue>
        </AttributeInstanceComponent>
        <AttributeInstanceComponent>
            <attribute>ProcessType</attribute>
            <attributeValue>A01</attributeValue>
        </AttributeInstanceComponent>
        <AttributeInstanceComponent>
            <attribute>TimeInterval</attribute>
            <attributeValue>{start_date}/{end_date}</attributeValue>
        </AttributeInstanceComponent>
        </StatusRequest_MarketDocument> 
        """
        # Get Data
        data = requests.post('https://web-api.tp.entsoe.eu/api', data=xml, headers=headers).text
        data = xmltodict.parse(data)["Publication_MarketDocument"]["TimeSeries"]
        points = []
        
        #Create Time Point
        time = datetime.strptime(start_date, "%Y-%m-%dT%H:%MZ")
        
        #Loop Through Points
        for Object in data:
            points = points + Object["Period"]["Point"]
        
        #Data to return
        formatedData = [[],[]]
        avg = 0
        
        #Store Points
        for i,point in enumerate(points):
            formatedData[0].append(float(point["price.amount"]))
            formatedData[1].append(time.strftime("%d/%m/%Y %H:%M"))
            time = time + timedelta(hours=1)
        
        #Calculate Measurements
        avg = sum(formatedData[0])/len(formatedData[0])
        
        formatedData.append(max(formatedData[0]))
        formatedData.append(min(formatedData[0]))
        formatedData.append(avg)
        
        formatedData = timeline_transform(formatedData, int(timeline))
        output.append(formatedData)
    return jsonify({"data": output})
    


if __name__ == '__main__':
    app.run(debug=True)