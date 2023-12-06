#include <Servo.h>

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
int limit_bucket_ladder_top = 8;
int limit_bucket_ladder_bottom = 10;
int limit_deposition_forward = 5;
int limit_actuator_extended = 12;
int limit_deposition_back = 13;

void setup() {
    Serial.begin(9600); // Open serial port 9600 bps
    Serial.setTimeout(5);
    myservo1.attach(9); // Attaches the servo on pin 9 to the servo object
    myservo2.attach(3); // Attaches the servo on pin 3 to the servo object

    // Set up pins to take input from Joule
    pinMode(9, INPUT);
    pinMode(3, INPUT);

    pinMode(limit_bucket_ladder_top, INPUT_PULLUP);
    pinMode(limit_bucket_ladder_bottom, INPUT_PULLUP);
    pinMode(limit_deposition_forward, INPUT_PULLUP);
    pinMode(limit_actuator_extended, INPUT_PULLUP);
    pinMode(limit_deposition_back, INPUT_PULLUP);

    pinMode(relay_1, OUTPUT);
    pinMode(relay_2, OUTPUT);

    digitalWrite(relay_1, LOW);
    digitalWrite(relay_2, LOW);
}

void loop() {
    check_limit_switches();
    if (Serial.available() >= 2) {
        // Read the incoming bytes
        int rlen = Serial.readBytes(buf, BUFFER_SIZE);
        if (rlen != BUFFER_SIZE) {
            return;
        }
        Serial.println("ACK");
        memcpy(&(current_message.FunctionCode), buf, sizeof(byte));
        memcpy(&(current_message.Degrees), buf+1, sizeof(byte));
        if (current_message.FunctionCode == 1) {
            myservo1.write(current_message.Degrees);
            delay(50); // Waits 50ms for the servo to reach the position
        } else if (current_message.FunctionCode == 2) {
            myservo2.write(current_message.Degrees);
            delay(50); // Waits 50ms for the servo to reach the position
        } else if (current_message.FunctionCode == 3) {
            // Actuator off
            digitalWrite(relay_1, LOW);
            digitalWrite(relay_2, LOW);
        } else if (current_message.FunctionCode == 4) {
            // Actuator reverse
            digitalWrite(relay_2, HIGH);
        } else if (current_message.FunctionCode == 5 && digitalRead(limit_actuator_extended) == LOW) {
            // Actuator forward
            digitalWrite(relay_1, HIGH);
        }
    }
}

void check_limit_switches() {
    if (digitalRead(limit_bucket_ladder_top) == HIGH) {
        Serial.println("Hit: limit_bucket_ladder_top");
    }
    if (digitalRead(limit_bucket_ladder_bottom) == HIGH) {
        Serial.println("Hit: limit_bucket_ladder_bottom");
    }
    if (digitalRead(limit_deposition_forward) == HIGH) {
        Serial.println("Hit: limit_deposition_forward");
    }
    if (digitalRead(limit_actuator_extended) == HIGH) { // && digitalRead(relay_1) == HIGH) {
        Serial.println("Hit: limit_actuator_extended");
        digitalWrite(relay_1, LOW);
        //digitalWrite(relay_2, LOW);
    }
    if (digitalRead(limit_deposition_back) == HIGH) {
        Serial.println("Hit: limit_deposition_back");
    }
}
