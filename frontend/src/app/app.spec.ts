import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { App } from './app';
import { NAV_ITEMS, routes } from './app.routes';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideRouter(routes)],
    }).compileComponents();
  });

  it('renders one menu link per nav item', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const links = (fixture.nativeElement as HTMLElement).querySelectorAll('mat-nav-list a');
    expect([...links].map((a) => a.getAttribute('href'))).toEqual(NAV_ITEMS.map((i) => '/' + i.path));
  });
});
