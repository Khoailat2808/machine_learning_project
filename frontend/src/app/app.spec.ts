import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { App } from './app';
import { NAV_ITEMS, routes } from './app.routes';

describe('App', () => {
  beforeEach(async () => {
    localStorage.setItem('username', 'marketer');
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideRouter(routes), provideHttpClient()],
    }).compileComponents();
  });

  afterEach(() => localStorage.clear());

  it('renders one menu link per nav item when logged in', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const links = (fixture.nativeElement as HTMLElement).querySelectorAll('mat-nav-list a');
    expect([...links].map((a) => a.getAttribute('href'))).toEqual(NAV_ITEMS.map((i) => '/' + i.path));
  });
});
