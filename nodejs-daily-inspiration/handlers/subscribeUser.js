const AWS = require("aws-sdk");
const USERS_TABLE = process.env.USERS_TABLE;
const dynamoDb = new AWS.DynamoDB.DocumentClient();

const uuid = require("uuid");
module.exports.subscribeUser = (event, context, callback) => {
  const data = JSON.parse(event.body);
  console.log("EVENT:::", data);

  const timestamp = new Date().getTime();

  if (typeof data.email !== "string") {
    console.error("Validation Failed");

    return;
  }
  const params = {
    TableName: USERS_TABLE,
    Item: {
      userId: uuid.v4(),
      email: data.email,
      subscriber: true,
      createdAt: timestamp,
      updatedAt: timestamp,
    },
  };

  // write the user to the database
  dynamoDb.put(params, (error, data) => {
    if (error) {
      console.error(error);
      callback(new Error(error));
      return;
    }
    //create a response
    const response = {
      statusCode: 200,
      body: JSON.stringify(data.Item),
    };
    callback(null, response);
  });
};