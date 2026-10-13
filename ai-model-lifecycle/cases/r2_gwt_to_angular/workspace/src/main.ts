// Fixed entry point: the app must export `AppComponent` from ./app/app.component
// and `appConfig` (an ApplicationConfig) from ./app/app.config.
import { bootstrapApplication } from '@angular/platform-browser';
import { AppComponent } from './app/app.component';
import { appConfig } from './app/app.config';

bootstrapApplication(AppComponent, appConfig).catch((err) => console.error(err));
