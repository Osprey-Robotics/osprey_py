//Limit Switches Input 
int limit_bucket_ladder_top = 8;
int limit_bucket_ladder_bottom = 10;
int limit_deposition_forward = 11; 
int limit_actuator_extended = 12; 
int limit_deposition_back = 13; 


void setup() {

  pinMode(limit_bucket_ladder_top, INPUT_PULLUP);
  pinMode(limit_bucket_ladder_bottom, INPUT_PULLUP);
  pinMode(limit_deposition_forward, INPUT_PULLUP);
  pinMode(limit_actuator_extended, INPUT_PULLUP);
  pinMode(limit_deposition_back, INPUT_PULLUP);
  Serial.begin(9600);

}

void loop() {
   if (digitalRead(limit_bucket_ladder_top) == HIGH) {
        Serial.println("Hit: limit_bucket_ladder_top");
        delay(100); //add delay if needed
    }
    if (digitalRead(limit_bucket_ladder_bottom) == HIGH) {
        Serial.println("Hit: limit_bucket_ladder_bottom");
    }
    if (digitalRead(limit_deposition_forward) == HIGH) {
        Serial.println("Hit: limit_deposition_forward");
    }
    if (digitalRead(limit_actuator_extended) == HIGH) { 
        Serial.println("Hit: limit_actuator_extended");
    }
    if (digitalRead(limit_deposition_back) == HIGH) {
        Serial.println("Hit: limit_deposition_back");
  delay(1000);

}
}