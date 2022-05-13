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

// Actuator constants
/***************************************************************************************************
 * When led 1 and 2 is on, actuator moves forward. When led 1 and 2 off, actuator moves backwards. *
 * When led 3 and 4 is on, the actuator moves. When either led 3 or 4 is off, actuator stops.      *
 ***************************************************************************************************/
const int DEBOUNCE_TIME = 50; // the time it takes for the button to rebound when released
//int actuatorForward = 13;
//int actuatorBackward = 12;
int limitSwitch = 11;
/*relay 1 and 2 controls forward and reverse, 3 and 4 both need to be "HIGH" to run actuators*/
int relay_1 = 7;
int relay_2 = 6;
int relay_3 = 5;
int relay_4 = 4;
int relay1And2State = LOW; // actuator default set to reverse "LOW"
int actuatorOn = HIGH;
int actuatorOff = LOW;

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

    //pinMode(actuatorForward, INPUT);
    //pinMode(actuatorBackward, INPUT);
    pinMode(limitSwitch, INPUT);

    pinMode(relay_1, OUTPUT);
    pinMode(relay_2, OUTPUT);
    pinMode(relay_3, OUTPUT);
    pinMode(relay_4, OUTPUT);
}

void loop() {
    if (Serial.available() > 0) {
        Limit_Switches(); //checks if the actuator can move
        // Read the incoming bytes
        int rlen = Serial.readBytes(buf, BUFFER_SIZE);
        current_message.FunctionCode = buf[0];
        current_message.Degrees = buf[1];
        // Prints the received data
        ardprintf("Received function %d with degrees %d", current_message.FunctionCode, current_message.Degrees);
        if (current_message.FunctionCode == 1) {
            myservo1.write(current_message.Degrees);
            delay(10); // Waits 10ms for the servo to reach the position
        } else if (current_message.FunctionCode == 2) {
            myservo2.write(current_message.Degrees);
            delay(10); // Waits 10ms for the servo to reach the position
        } else if (current_message.FunctionCode == 3) {
            Forward_Actuator();
            delay(1000); // Waits 1000ms for the actuator to reach the position
            digitalWrite(relay_4, actuatorOff); // stops actuator when button released
        } else if (current_message.FunctionCode == 4) {
            Reverse_Actuator();
            delay(1000); // Waits 1000ms for the actuator to reach the position
            digitalWrite(relay_4, actuatorOff);
        }
    }
}

/********************************************************************************
 * checks if limit switch is pressed then opens the third relay.                *
 * if neither is pressed then it does nothing.                                  *
 ********************************************************************************/
void Limit_Switches() {
    if (digitalRead(limitSwitch) == HIGH) {
        digitalWrite(relay_3, actuatorOff);
    } else {
        digitalWrite(relay_3, actuatorOn);
    }
    delay(DEBOUNCE_TIME);
}

/**************************************************************************************
 * checks if the forward button is pressed and makes the actuator move forward "HIGH" *
 * then opens relay 4 when released. If not pressed down then it does nothing.        *
 **************************************************************************************/
void Forward_Actuator() {
    Limit_Switches();
    // relay1And2State makes the actuator move forward when == "HIGH"
    if (relay1And2State == LOW) {
        Change_Relay_State();
        digitalWrite(relay_1, relay1And2State);
        digitalWrite(relay_2, relay1And2State);
    } else {
        //doesn't need to write to relay 1 and 2 because they're already set to forward "HIGH"
        digitalWrite(relay_4, actuatorOn);
    }
    //delay(DEBOUNCE_TIME);
    //digitalWrite(relay_4, actuatorOff); // stops actuator when button released
}

/*************************************************************************************
 * checks if the reverse button is pressed and makes the actuator move reverse "LOW" *
 * then opens relay 4 when released. If not pressed down then it does nothing.       *
 *************************************************************************************/
void Reverse_Actuator() {
    Limit_Switches(); // probably needs to be removed because can brick the actuator if limit switch can't be reset
    // relay1And2State makes the actuator move backwards when == "LOW"
    if (relay1And2State == HIGH) {
        Change_Relay_State();
        digitalWrite(relay_1, relay1And2State);
        digitalWrite(relay_2, relay1And2State);
    } else {
        //doesn't need to write to relay 1 and 2 because they're already set to reverse "LOW"
        digitalWrite(relay_4, actuatorOn);
    }
    //delay(DEBOUNCE_TIME);
    //digitalWrite(relay_4, actuatorOff);
}

/***************************************************************************************
 * changes the variable relayState to "LOW" if it is "HIGH" and "HIGH" if it is "LOW". *
 ***************************************************************************************/
void Change_Relay_State() {
    if (relay1And2State == LOW) {
        relay1And2State = HIGH;
    } else {
        relay1And2State = LOW;
    }
}
