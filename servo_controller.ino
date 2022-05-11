#include <Servo.h>
#ifndef ARDPRINTF
#define ARDPRINTF
#define ARDBUFFER 16
#include <stdarg.h>
#include <Arduino.h>

int ardprintf(char *str, ...)
{
  int i, count=0, j=0, flag=0;
  char temp[ARDBUFFER+1];
  for(i=0; str[i]!='\0';i++)  if(str[i]=='%')  count++;

  va_list argv;
  va_start(argv, count);
  for(i=0,j=0; str[i]!='\0';i++)
  {
    if(str[i]=='%')
    {
      temp[j] = '\0';
      Serial.print(temp);
      j=0;
      temp[0] = '\0';

      switch(str[++i])
      {
        case 'd': Serial.print(va_arg(argv, int));
                  break;
        case 'l': Serial.print(va_arg(argv, long));
                  break;
        case 'f': Serial.print(va_arg(argv, double));
                  break;
        case 'c': Serial.print((char)va_arg(argv, int));
                  break;
        case 's': Serial.print(va_arg(argv, char *));
                  break;
        default:  ;
      };
    }
    else 
    {
      temp[j] = str[i];
      j = (j+1)%ARDBUFFER;
      if(j==0) 
      {
        temp[ARDBUFFER] = '\0';
        Serial.print(temp);
        temp[0]='\0';
      }
    }
  };
  Serial.println();
  return count + 1;
}
#undef ARDBUFFER
#endif

// Constants
Servo myservo1;
Servo myservo2;
struct message_frame {
  byte FunctionCode;
  byte Degrees; // char
  //byte Checksum;
} data;
static message_frame current_message {
  .FunctionCode = 0,
  .Degrees = 0
};
const int BUFFER_SIZE = 2;
char buf[BUFFER_SIZE];
int readByte = 0; // Initialize Joule input
int pos_x = 0; // X axis movement
int pos_y = 0; // Y axis movement

void setup() {
  Serial.begin(9600); // Open serial port 9600 bps
  //Serial.setTimeout(1);
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
  //int move_cam = 1; // increment or decrement the position by 1

  // check if data is available
  if (Serial.available() > 0) {
    // read the incoming bytes:
    int rlen = Serial.readBytes(buf, BUFFER_SIZE);
    current_message.FunctionCode = buf[0];
    current_message.Degrees = buf[1];

    // prints the received data
    ardprintf("Received function %d with degrees %d", current_message.FunctionCode, current_message.Degrees);
    if (current_message.FunctionCode == 1) {
      /*
      for (pos_x = 90; pos_x <= 180; pos += 1) { // goes from 0 degrees to 180 degrees 
        if (readByte = 1) {
          pos_x = pos_x - move_cam;
        } else if (readByte = 2) {
          pos_x = pos_x + move_cam;
        }
        // left right servo
      }
      */
      myservo2.write(current_message.Degrees);
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
