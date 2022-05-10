#include <Servo.h>

// create servo objects
Servo myservo1;
Servo myservo2;

int readByte = 0; // initialize joule input

int pos = 0;    // variable to store the servo position

void setup() {
  Serial.begin(9600); // open serial port 9600 bps
  myservo1.attach(9);  // attaches the servo on pin 9 to the servo object
  myservo2.attach(3);  // attaches the servo on pin 3 to the servo object
  
  // set up pins to take input from joule
  pinMode(9, INPUT);
  pinMode(3, INPUT);
}

void loop() {
  
    int pos_x = 0;
    int pos_y = 0;

// 1 is left, 2 is right
 if ((readByte = 1) || (readByte = 2)) {
  for (pos_x = 90; pos_x <= 180; pos += 1) { // goes from 0 degrees to 180 degrees 
    if (readByte = 1) {
   pos_x = pos_x - 1 ;
    }
    else if (readByte = 2) {
   pos_x = pos_x + 1 ;
    }
    // left right servo
      myservo1.write(pos_x);
   }
 }
 // 3 is down, 4 is up
   else if((readByte = 3) || (readByte = 4)) {
  for (pos_y = 90; pos_y <= 180; pos+= 1) {
    if (readByte = 3){
    pos_y = pos_y - 1;
    }
    else if (readByte = 4){
    pos_y = pos_y + 1;
    }
  }
  // up down servo
    myservo2.write(pos_y);
   }            

  delay(10);                       // waits 10ms for the servo to reach the position
  }
