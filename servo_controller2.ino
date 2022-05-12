#include <Servo.h>
 //#ifndef ARDPRINTF
//#define ARDPRINTF
#define ARDBUFFER 16#include <stdarg.h>

#include <Arduino.h>

//int ardprintf(char *str, ...)
//{
//  int i, count=0, j=0, flag=0;
//  char temp[ARDBUFFER+1];
//  for(i=0; str[i]!='\0';i++)  if(str[i]=='%')  count++;
//
//  va_list argv;
//  va_start(argv, count);
//  for(i=0,j=0; str[i]!='\0';i++)
//  {
//    if(str[i]=='%')
//    {
////      temp[j] = '\0';
////      Serial.print(temp);
////      j=0;
////      temp[0] = '\0';
//
////      switch(str[++i])
////      {
////        case 'd': Serial.print(va_arg(argv, int));
////                  break;
////        case 'l': Serial.print(va_arg(argv, long));
////                  break;
////        case 'f': Serial.print(va_arg(argv, double));
////                  break;
////        case 'c': Serial.print((char)va_arg(argv, int));
////                  break;
////        case 's': Serial.print(va_arg(argv, char *));
////                  break;
////        default:  ;
////      };
//    }
//    else 
//    {
//      temp[j] = str[i];
//      j = (j+1)%ARDBUFFER;
//      if(j==0) 
//      {
//        temp[ARDBUFFER] = '\0';
////        Serial.print(temp);
//        temp[0]='\0';
//      }
//    }
//  };
////  Serial.println();
//  return count + 1;
//}
//#undef ARDBUFFER
//#endif

// Constants
Servo myservo1;
Servo myservo2;
struct message_frame {
  byte FunctionCode;
  byte Degrees; // char
  //byte Checksum;
}
data;
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

  // check if data is available
  if (Serial.available() > 0) {
    // read the incoming bytes:
    int rlen = Serial.readBytes(buf, BUFFER_SIZE);
    current_message.FunctionCode = buf[0];
    current_message.Degrees = buf[1];

    // prints the received data
    //    ardprintf("Received function %d with degrees %d", current_message.FunctionCode, current_message.Degrees);
    if (current_message.FunctionCode == 1) {
      myservo1.write(current_message.Degrees);
    } else if (current_message.FunctionCode == 2) {
      myservo2.write(current_message.Degrees);
    }
    delay(10); // waits 10ms for the servo to reach the position
  }
}
