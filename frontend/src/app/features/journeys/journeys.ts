import { CurrencyPipe, DecimalPipe, LowerCasePipe, PercentPipe } from '@angular/common';
import { httpResource } from '@angular/common/http';
import { Component, computed } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { RouterLink } from '@angular/router';

import { environment } from '../../../environments/environment';
import { JourneysResponse } from '../../core/models';
import { LEVEL_LABELS } from '../../shared/constants';
import { JourneyTimeline } from '../../shared/journey-timeline';

// FR-SEG-01: 6 lộ trình theo phân khúc; ngưỡng τ, P33, P67 chỉ đọc
@Component({
  selector: 'app-journeys',
  imports: [
    CurrencyPipe, DecimalPipe, LowerCasePipe, PercentPipe, RouterLink,
    MatButtonModule, MatCardModule, MatIconModule, MatProgressBarModule, MatTooltipModule, JourneyTimeline,
  ],
  templateUrl: './journeys.html',
  styleUrl: './journeys.css',
})
export class Journeys {
  protected readonly levels = LEVEL_LABELS;
  protected readonly data = httpResource<JourneysResponse>(() => `${environment.apiUrl}/journeys`);

  protected readonly totalVar = computed(() =>
    this.data.hasValue() ? this.data.value().journeys.reduce((s, j) => s + j.value_at_risk, 0) : 0,
  );
}
