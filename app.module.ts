// app.module.ts
// Demonstrates proper Angular module structure, imports, and dependency injection

import { NgModule }              from '@angular/core';
import { BrowserModule }         from '@angular/platform-browser';
import { HttpClientModule }      from '@angular/common/http';
import { ReactiveFormsModule }   from '@angular/forms';

import { AppRoutingModule }      from './app-routing.module';
import { AppComponent }          from './app.component';
import { TransactionMonitorComponent }
  from './components/transaction-monitor/transaction-monitor.component';
import { RiskDashboardComponent }
  from './components/risk-dashboard/risk-dashboard.component';
import { FraudAnalyticsService } from './services/fraud-analytics.service';
import { FlaggedCountPipe }      from './pipes/flagged-count.pipe';

@NgModule({
  declarations: [
    AppComponent,
    TransactionMonitorComponent,
    RiskDashboardComponent,
    FlaggedCountPipe,
  ],
  imports: [
    BrowserModule,
    HttpClientModule,
    ReactiveFormsModule,
    AppRoutingModule,
  ],
  providers: [
    FraudAnalyticsService,
  ],
  bootstrap: [AppComponent],
})
export class AppModule {}
