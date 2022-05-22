#include <Servo.h>
#ifndef ARDPRINTF
#define ARDPRINTF
#define ARDBUFFER 16
#include <stdarg.h>
#include <Arduino.h>

int ardprintf(char * str, ...) {
    int i, count = 0, j = 0, flag = 0;
    char temp[ARDBUFFER + 1];
    for (i = 0; str[i] != '\0'; i++)
        if (str[i] == '%') count++;

    va_list argv;
    va_start(argv, count);
    for (i = 0, j = 0; str[i] != '\0'; i++) {
        if (str[i] == '%') {
            temp[j] = '\0';
            Serial.print(temp);
            j = 0;
            temp[0] = '\0';

            switch (str[++i]) {
            case 'd':
                Serial.print(va_arg(argv, int));
                break;
            case 'l':
                Serial.print(va_arg(argv, long));
                break;
            case 'f':
                Serial.print(va_arg(argv, double));
                break;
            case 'c':
                Serial.print((char) va_arg(argv, int));
                break;
            case 's':
                Serial.print(va_arg(argv, char * ));
                break;
            default:
                ;
            };
        } else {
            temp[j] = str[i];
            j = (j + 1) % ARDBUFFER;
            if (j == 0) {
                temp[ARDBUFFER] = '\0';
                Serial.print(temp);
                temp[0] = '\0';
            }
        }
    };
    Serial.println();
    return count + 1;
}
#undef ARDBUFFER
#endif

// Main constants
Servo myservo1;
Servo myservo2;
struct message_frame {
    byte FunctionCode;
    byte Degrees;
    //byte Checksum;
}
data;
static message_frame current_message {
    .FunctionCode = 0,
    .Degrees = 0
};
const int BUFFER_SIZE = 2;
char buf[BUFFER_SIZE];
int relay_1 = 7;
int relay_2 = 6;

void setup() {
    Serial.begin(9600); // Open serial port 9600 bps
    //Serial.setTimeout(1);
    myservo1.attach(9); // Attaches the servo on pin 9 to the servo object
    myservo2.attach(3); // Attaches the servo on pin 3 to the servo object

    // Set up pins to take input from Joule
    pinMode(9, INPUT);
    pinMode(3, INPUT);

    pinMode(relay_1, OUTPUT);
    pinMode(relay_2, OUTPUT);

    digitalWrite(relay_1, LOW);
    digitalWrite(relay_2, LOW);
}

void loop() {
    if (Serial.available() > 0) {
        // Read the incoming bytes
        int rlen = Serial.readBytes(buf, BUFFER_SIZE);
        if (rlen != BUFFER_SIZE) {
            return;
        }
        memcpy(&(current_message.FunctionCode), buf, sizeof(byte));
        memcpy(&(current_message.Degrees), buf+1, sizeof(byte));
        // Prints the received data
        ardprintf("Received function %d with degrees %d", current_message.FunctionCode, current_message.Degrees);
        if (current_message.FunctionCode == 1) {
            myservo1.write(current_message.Degrees);
            delay(10); // Waits 10ms for the servo to reach the position
        } else if (current_message.FunctionCode == 2) {
            myservo2.write(current_message.Degrees);
            delay(10); // Waits 10ms for the servo to reach the position
        } else if (current_message.FunctionCode == 3) {
            // Actuator off
            digitalWrite(relay_1, LOW);
            digitalWrite(relay_2, LOW);
        } else if (current_message.FunctionCode == 4) {
            // Actuator forward
            digitalWrite(relay_1, HIGH);
        } else if (current_message.FunctionCode == 5) {
            // Actuator reverse
            digitalWrite(relay_2, HIGH);
        }
    }
}
