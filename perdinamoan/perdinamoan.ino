#include <Keypad.h>
#include <LiquidCrystal_I2C.h>
LiquidCrystal_I2C lcd(0x27, 16, 2);

const byte ROWS = 4;  // Four rows
const byte COLS = 3;  // Three columns
char keys[ROWS][COLS] = {
  { '1', '2', '3' },
  { '4', '5', '6' },
  { '7', '8', '9' },
  { '*', '0', '#' }
};
byte rowPins[ROWS] = { 5, 4, 3, 12 };  // Connect to the row pinouts of the keypad
byte colPins[COLS] = { 8, 7, 6 };     // Connect to the column pinouts of the keypad

Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

const int motorEnablePin = 11;
const int motorPin1 = 10;
const int motorPin2 = 9;

String rpmInput = "";
bool newInput = false;

int currentRPM = 0;  // Variable to hold the current RPM value

const byte PulsesPerRevolution = 2;
const unsigned long ZeroTimeout = 100000;
const byte numReadings = 2;

volatile unsigned long LastTimeWeMeasured;
volatile unsigned long PeriodBetweenPulses = ZeroTimeout + 1000;
volatile unsigned long PeriodAverage = ZeroTimeout + 1000;
unsigned long FrequencyRaw;
unsigned long FrequencyReal;
unsigned long RPM_read;
unsigned int PulseCounter = 1;
unsigned long PeriodSum;

unsigned long LastTimeCycleMeasure = LastTimeWeMeasured;
unsigned long CurrentMicros = micros();
unsigned int AmountOfReadings = 1;
unsigned int ZeroDebouncingExtra;
unsigned long readings[numReadings];
unsigned long readIndex;
unsigned long total;
unsigned long average;

int rpm;

void Pulse_Event() {
  PeriodBetweenPulses = micros() - LastTimeWeMeasured;
  LastTimeWeMeasured = micros();
  if (PulseCounter >= AmountOfReadings) {
    PeriodAverage = PeriodSum / AmountOfReadings;
    PulseCounter = 1;
    PeriodSum = PeriodBetweenPulses;

    int RemapedAmountOfReadings = map(PeriodBetweenPulses, 40000, 5000, 1, 10);
    RemapedAmountOfReadings = constrain(RemapedAmountOfReadings, 1, 10);
    AmountOfReadings = RemapedAmountOfReadings;
  } else {
    PulseCounter++;
    PeriodSum = PeriodSum + PeriodBetweenPulses;
  }
}

void setup() {
  Serial.begin(9600);
  pinMode(motorEnablePin, OUTPUT);
  pinMode(motorPin1, OUTPUT);
  pinMode(motorPin2, OUTPUT);

  lcd.init();
  lcd.backlight();
  attachInterrupt(0, Pulse_Event, RISING);
  // attachInterrupt(0, isrCount, FALLING);  //interupt signal to pin 2
  delay(500);
}

void loop() {

 static int lastRPMInput = 0;
  LastTimeCycleMeasure = LastTimeWeMeasured;
  CurrentMicros = micros();
  if (CurrentMicros < LastTimeCycleMeasure) {
    LastTimeCycleMeasure = CurrentMicros;
  }
  FrequencyRaw = 10000000000 / PeriodAverage;
  if (PeriodBetweenPulses > ZeroTimeout - ZeroDebouncingExtra || CurrentMicros - LastTimeCycleMeasure > ZeroTimeout - ZeroDebouncingExtra) {
    FrequencyRaw = 0;  // Set frequency as 0.
    ZeroDebouncingExtra = 2000;
  } else {
    ZeroDebouncingExtra = 0;
  }
  FrequencyReal = FrequencyRaw / 10000;

  RPM_read = FrequencyRaw / PulsesPerRevolution * 60;
  RPM_read = RPM_read / 10000;
  total = total - readings[readIndex];
  readings[readIndex] = RPM_read;
  total = total + readings[readIndex];
  readIndex = readIndex + 1;

  if (readIndex >= numReadings) {
    readIndex = 0;
  }
  average = total / numReadings;

  // Handle keypad input
  char key = keypad.getKey();
  if (key) {
    if (key == '#') {
      if (rpmInput.length() > 0) {
        int rpm = rpmInput.toInt();
        lastRPMInput = rpm;  // Store the latest RPM input
        setMotorSpeed(rpm);
        rpmInput = "";
        newInput = false;
      }
    } else if (key == '*') {
      rpmInput = "";
      newInput = false;
    } else {
      rpmInput += key;
      newInput = true;
    }
    Serial.println(rpmInput);  // Print the concatenated key inputs
  }

  // Handle serial input
  if (Serial.available() > 0) {
    String serialInput = Serial.readStringUntil('#');
    int rpm = serialInput.toInt();
    setMotorSpeed(rpm);
    Serial.print("Received RPM from serial: ");
    Serial.println(rpm);
  }

  // Send current RPM to serial port for monitoring
  static unsigned long lastMillis = 0;
  if (millis() - lastMillis >= 1000) {
    lastMillis = millis();
    Serial.print("Set point: ");
    Serial.println(currentRPM);
    Serial.print("Output: ");
    Serial.println(RPM_read);
  }

  lcd.setCursor(0, 0);
  lcd.print("SET POINT: ");
  lcd.print(currentRPM);
  lcd.print("     ");

  lcd.setCursor(0, 1);
  lcd.print("OUTPUT: ");
  // int rpm_read_rounded = RPM_read/2.4;
  int rpm_read_rounded = RPM_read;
  lcd.print((int)rpm_read_rounded);

  lcd.print("     ");
}

void setMotorSpeed(int rpm) {
  // Map RPM to PWM value (0-255)
  int pwmValue = map(rpm, 0, 5000, 40, 255);

  analogWrite(motorEnablePin, pwmValue);
  digitalWrite(motorPin1, HIGH);
  digitalWrite(motorPin2, LOW);

  currentRPM = rpm;  // Update the current RPM value

  Serial.print("Motor RPM set to: ");
  Serial.println(rpm);
}

int getCurrentRPM() {
  // Return the current RPM value
  return currentRPM;
}
