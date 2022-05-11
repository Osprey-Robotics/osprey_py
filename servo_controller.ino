#include <Servo.h>

// create servo objects
Servo myservo1;
Servo myservo2;

int readByte = 0; // initialize joule input
int move_cam = 10; // increment or decrement the position by 1
int pos_x = 0; // x axis movement
int pos_y = 0; // y axis movement
int x = 0;
int getVal = 0;

void setup() {
  Serial.begin(115200); // open serial port 115200 bps
  Serial.setTimeout(1);
  myservo1.attach(9); // attaches the servo on pin 9 to the servo object
  myservo2.attach(3); // attaches the servo on pin 3 to the servo object
  readByte = Serial.read();
  getVal = Serial.parseInt();

  // set up pins to take input from joule
  pinMode(9, INPUT);
  pinMode(3, INPUT);
}

void loop() {
  Serial.println("Hello from arduino");

  if (Serial.available() > 0) {

    if (getVal = 1) {
      pos_x = pos_x - move_cam;
      myservo1.write(pos_x);
    } else if (getVal = 2) {
      pos_x = pos_x + move_cam;
      myservo1.write(pos_x);
    } else if (getVal = 3) {
      pos_y = pos_y - move_cam;
      myservo2.write(pos_y);
    } else if (readByte = 4) {
      pos_y = pos_y + move_cam;
      myservo2.write(pos_y);
    }
  }


  delay(10); // waits 10ms for the servo to reach the position
}
