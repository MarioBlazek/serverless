const aws = require("aws-sdk");
const sns = new aws.SNS();
const axios = require("axios");

const publishToSNS = (message) =>
    sns.publish({
        Message: message,
        TopicArn: process.env.SNS_TOPIC_ARN,
    }).promise();

const buildEmailBody = (id, form) => {
    return `
        Message: ${form.message}
        Name: ${form.name}
        Email: ${form.email}
        Service information: ${id.sourceIp} - ${id.userAgent}
    `
}

module.exports.staticMailer = async (event) => {
    console.log("EVENT::", event);
    const data = JSON.parse(event.body);
    const emailBody = buildEmailBody(event.requestContext.identity, data);

    await publishToSNS(emailBody);

    await axios.post(
        "subscribe URL",
        {
            email: data.email
        }
    ).then(function(response) {
        console.log(response);
    }).catch(function(error) {
        console.log("Error subscribing:::" + error);
    })


    return {
        statusCode: 200,
        headers: {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": false,
        },
        body: JSON.stringify({message: "OK"})
    }
}