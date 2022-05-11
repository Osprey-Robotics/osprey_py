#include <Servo.h>

// Create servo objects
Servo myservo1;
Servo myservo2;

const int BUFFER_SIZE = 1;
char buf[BUFFER_SIZE];
int readByte = 0; // Initialize Joule input
int pos_x = 0; // X axis movement
int pos_y = 0; // Y axis movement

void setup() {
  Serial.begin(9600); // Open serial port 9600 bps
  Serial.setTimeout(1);
  myservo1.attach(9); // Attaches the servo on pin 9 to the servo object
  myservo2.attach(3); // Attaches the servo on pin 3 to the servo object

  // Set up pins to take input from Joule
  pinMode(9, INPUT);
  pinMode(3, INPUT);

  // Sets up 5V power
  pinMode(2, OUTPUT);
  digitalWrite(2, HIGH);
}

void loop() {
  // getVal = Serial.parseInt();
  int move_cam = 1; // increment or decrement the position by 1
  int pos_x = 0; // x axis movement
  int pos_y = 0; // y axis movement

  // check if data is available
  if (Serial.available() > 0) {
    // read the incoming bytes:
    int rlen = Serial.readBytes(buf, BUFFER_SIZE);

    // prints the received data
    Serial.println("Hello from arduino");
    for (int i = 0; i < rlen; i++)
      Serial.print(buf[i]);
    
    if ((readByte = 1) || (readByte = 2)) {
      Serial.print("First condition: ");
      for (pos_x = 90; pos_x <= 180; pos += 1) { // goes from 0 degrees to 180 degrees 
        if (readByte = 1) {
          pos_x = pos_x - move_cam;
        } else if (readByte = 2) {
          pos_x = pos_x + move_cam;
        }
        // left right servo
        myservo1.write(pos_x);
      }
    }
    /*
    // 3 is down, 4 is up
    else if ((readByte = 3) || (readByte = 4)) {
      for (pos_y = 90; pos_y <= 180; pos += 1) {
        if (readByte = 3) {
          pos_y = pos_y - move_cam;
        } else if (readByte = 4) {
          pos_y = pos_y + move_cam;
        }
      }
      // up down servo
      myservo2.write(pos_y);
    }
    */

    delay(10); // waits 10ms for the servo to reach the position
  }
}
